
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error
from sqlalchemy import create_engine, text\

# --- CONFIGURATION ---

# Database connection details - REPLACE WITH YOUR ACTUAL CREDENTIALS
DB_CONFIG = {
    'user': 'your_username',
    'password': 'your_password',
    'host': 'your_host',
    'port': '5432',
    'database': 'your_database_name'
}
DB_DATA_TABLE_NAME = 'house_prices'
DB_MODEL_TABLE_NAME = 'ml_models'
MODEL_NAME_IN_DB = 'house_price_predictor_model'

def get_db_engine():
    """
    Establishes a connection engine to the PostgreSQL database.
    """
    try:
        conn_str = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        return create_engine(conn_str)
    except Exception as e:
        print(f"Error creating database engine: {e}")
        return None

def create_model_table_if_not_exists(engine):
    """
    Creates the ml_models table if it doesn't already exist,
    now including a column for RMSE score.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {DB_MODEL_TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    model_name VARCHAR(255) NOT NULL,
                    model_data BYTEA NOT NULL,
                    rmse_score FLOAT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            connection.commit()
        print(f"Table {DB_MODEL_TABLE_NAME} ensured to exist with rmse_score column.")
    except Exception as e:
        print(f"Error creating model table: {e}")

# --- BUTTON 1: RETRAIN MODEL ---
def train_model():
    """
    FUNCTION FOR THE 'RETRAIN' BUTTON:
    Splits data into training and testing sets to provide a realistic RMSE.
    """
    engine = get_db_engine()
    if engine is None:
        return "Error: Could not connect to the database."

    create_model_table_if_not_exists(engine)

    try:
        # 1. Load data from DB
        df = pd.read_sql(f"SELECT * FROM {DB_DATA_TABLE_NAME}", engine)

        # 2. Basic cleaning
        df = df.drop(['id', 'date'], axis=1, errors='ignore')

        # 3. Separate features and target
        X = df.drop('price', axis=1)
        y = df['price']

        # 4. SPLIT DATA: 80% for training, 20% for testing
        # We use a fixed random_state for reproducibility
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 5. Target transformation on the training and test labels
        y_train_log = np.log1p(y_train)

        # 6. Define Preprocessing (Kept identical to your original logic)
        categorical_features = ['waterfront', 'condition']
        numerical_features = [f for f in X.select_dtypes(include=np.number).columns if f not in categorical_features]

        numeric_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])

        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ])

        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numerical_features),
                ('cat', categorical_transformer, categorical_features)
            ]
        )

        # 7. Create Pipeline
        model_pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', GradientBoostingRegressor(
                n_estimators=200, 
                learning_rate=0.1, 
                max_depth=5, 
                random_state=42
            ))
        ])

        # 8. Fit ONLY on the Training Data
        model_pipeline.fit(X_train, y_train_log)

        # 9. EVALUATE on the Test Data (Unseen by the model)
        y_test_pred_log = model_pipeline.predict(X_test)
        y_test_pred = np.expm1(y_test_pred_log)
        
        # This RMSE is now a reliable indicator of real-world performance
        rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

        # 10. Serialize and Save
        serialized_model = joblib.dumps(model_pipeline)

        with engine.connect() as connection:
            connection.execute(text(f"""
                INSERT INTO {DB_MODEL_TABLE_NAME} (model_name, model_data, rmse_score)
                VALUES (:model_name, :model_data, :rmse_score);
            """), {'model_name': MODEL_NAME_IN_DB, 'model_data': serialized_model, 'rmse_score': rmse})
            connection.commit()

        return f"Success: Model retrained. Test RMSE: {rmse:.2f}. New version saved."

    except Exception as e:
        return f"Error during training: {str(e)}"

# --- BUTTON 2: PREDICT PRICE ---
def predict_price(house_characteristics: dict):
    """
    FUNCTION FOR THE 'PREDICT' BUTTON:
    Loads the best performing saved pipeline (lowest RMSE) from the database,
    applies preprocessing, and returns the estimated price.
    """
    engine = get_db_engine()
    if engine is None:
        return "Error: Could not connect to the database."

    try:
        # 1. Load the best performing serialized model from the database
        with engine.connect() as connection:
            model_record = connection.execute(text(f"""
                SELECT model_data FROM {DB_MODEL_TABLE_NAME}
                WHERE model_name = :model_name
                ORDER BY rmse_score ASC, last_updated DESC
                LIMIT 1;
            """), {'model_name': MODEL_NAME_IN_DB}).fetchone()

            if not model_record:
                return "Error: No model found in database. Please press the 'Retrain' button first."
            serialized_model = model_record[0]

        # 2. Deserialize the model
        model_pipeline = joblib.loads(serialized_model)

        # 3. Convert input to DataFrame
        input_df = pd.DataFrame([house_characteristics])

        # 4. Predict (Pipeline automatically applies the saved preprocessing)
        predicted_log_price = model_pipeline.predict(input_df)

        # 5. Reverse the log transformation to get the actual price
        final_price = np.expm1(predicted_log_price[0])

        return round(final_price, 2)

    except Exception as e:
        return f"Error during prediction: {str(e)}"

