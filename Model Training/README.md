### Dataset Access
To keep the repository lightweight and follow best practices, the **`house_prices.csv`** dataset is **not** included in this repository. 
* **Source:** [dataset](https://www.kaggle.com/datasets/alyelbadry/house-pricing-dataset?resource=download)
* **Setup:** Please download the dataset and place it in the root directory of this project before running the training scripts.

### Exploratory Data Analysis (EDA)
The file `house_prices_eda.ipynb` contains a comprehensive analysis of the house price features, including:
* Correlation matrices and feature importance.
* Handling of missing values and outliers.
* Data visualization and distribution plots.

### Model Training & Storage

The training process is fully automated through the `train_model()` function.

**Workflow:**
1. Data is loaded directly from the PostgreSQL database.
2. Basic cleaning is applied (dropping irrelevant columns like `id`, `date`).
3. The dataset is split:
   - 80% training
   - 20% testing
4. Target variable (`price`) is log-transformed using `log1p`.
5. A preprocessing pipeline is applied:
   - Numerical features → imputation + scaling
   - Categorical features → imputation + one-hot encoding
6. A `GradientBoostingRegressor` model is trained.
7. Model performance is evaluated using RMSE on unseen test data.
8. The trained pipeline is serialized and stored in the database.

Each trained model version is saved along with:
- RMSE score
- Timestamp

This allows versioning and selection of the best-performing model.

---

### Model Selection Strategy

When making predictions, the system automatically selects:

- The model with the **lowest RMSE**
- If multiple models have similar RMSE → the **most recent one**

This ensures optimal prediction performance without manual intervention.

---

### Prediction Pipeline

The `predict_price()` function handles inference.

**Steps:**
1. Loads the best model from the database.
2. Deserializes the saved pipeline.
3. Converts user input into a DataFrame.
4. Applies the same preprocessing used during training.
5. Predicts the log-price and converts it back to real price.

**Important:**  
Because preprocessing is embedded in the pipeline, input data must match the training schema (same feature names).

---

### Database Schema

#### Table: `house_prices`
Stores the dataset used for training.

#### Table: `ml_models`
Stores trained models.

| Column         | Type      | Description                |
|----------------|----------|----------------------------|
| id             | SERIAL   | Primary key                |
| model_name     | VARCHAR  | Model identifier           |
| model_data     | BYTEA    | Serialized model (joblib)  |
| rmse_score     | FLOAT    | Model performance metric   |
| last_updated   | TIMESTAMP| Training timestamp         |