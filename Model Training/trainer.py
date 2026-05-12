"""
Retraining script -- runs as a FastAPI background task.

Flow:
  1. Pull training_data from PostgreSQL
  2. Train LightGBM with 24 features (derived from 21 original columns)
  3. Evaluate on 20% test split
  4. Save .pkl to /tmp -> upload to MinIO -> delete /tmp
  5. INSERT into run_history (is_active=True if beats current)
  6. POST /reload-model -> hot-swap in-memory model
"""
import os
import uuid
import joblib
import requests
import numpy as np
import pandas as pd

from datetime import datetime
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sqlalchemy import create_engine, text

from storage import upload_model

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hpa:hpa@localhost:5432/hpa")

# Must match FEATURE_NAMES in model_loader.py
FEATURE_COLS = [
    "bedrooms",
    "bathrooms",
    "sqft_living",
    "sqft_lot",
    "floors",
    "view",
    "grade",
    "sqft_above",
    "sqft_basement",
    "zipcode",
    "lat",
    "long",
    "sqft_living15",
    "sqft_lot15",
    "house_age",
    "renovated",
    "years_since_renovation",
    "total_sqft",
    "has_basement",
    "price_per_sqft_area",
    "bath_per_bed",
    "living_lot_ratio",
    "condition_enc",
    "waterfront_enc",
]
TARGET_COL = "price"


def _load_training_data(engine) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM training_data", engine)

    # Derived features
    current_year = datetime.now().year
    df["house_age"] = current_year - df["yr_built"]
    df["renovated"] = (df["yr_renovated"] > 0).astype(int)
    df["years_since_renovation"] = np.where(
        df["yr_renovated"] > 0,
        current_year - df["yr_renovated"],
        df["house_age"]
    )
    df["total_sqft"] = df["sqft_above"] + df["sqft_basement"]
    df["has_basement"] = (df["sqft_basement"] > 0).astype(int)
    df["price_per_sqft_area"] = df["sqft_living"] / (df["sqft_lot"] + 1)
    df["bath_per_bed"] = df["bathrooms"] / (df["bedrooms"] + 1)
    df["living_lot_ratio"] = df["sqft_living"] / (df["sqft_lot"] + 1)

    # Encode condition (ordinal)
    condition_map = {
        "Poor": 1, "Fair": 2, "Average": 3, "Good": 4, "Very Good": 5
    }
    df["condition_enc"] = df["condition"].map(condition_map).fillna(3).astype(int)

    # Encode waterfront
    df["waterfront_enc"] = df["waterfront"].map({"N": 0, "Y": 1}).fillna(0).astype(int)

    # Drop original string columns
    df = df.drop(columns=["yr_built", "yr_renovated", "condition", "waterfront"], errors="ignore")

    return df


def run_retrain():
    start = datetime.now()
    version = start.strftime("%Y%m%d_%H%M%S")
    print(f"\nRetraining started -- version {version}")

    engine = create_engine(DATABASE_URL)

    try:
        df = _load_training_data(engine)
        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        dataset_size = len(df)
        print(f"   Dataset: {dataset_size} rows")

        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = LGBMRegressor(
            n_estimators=500,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=42,
            verbose=-1,
        )
        model.fit(X_train, y_train)

        accuracy = float(r2_score(y_test, model.predict(X_test)))
        duration = datetime.now() - start
        print(f"   R2 accuracy: {accuracy:.4f} | duration: {duration}")

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': FEATURE_COLS,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        print("   Top 5 Feature Importances:")
        print(feature_importance.head(5).to_string(index=False))

        # Save to /tmp then upload to MinIO
        tmp_path = f"/tmp/lgbm_{version}.pkl"
        joblib.dump(model, tmp_path)
        s3_uri = upload_model(tmp_path, f"models/lgbm_{version}.pkl")
        os.remove(tmp_path)
        print(f"   Uploaded to {s3_uri}")

        # Check if this beats the current active model
        with engine.connect() as conn:
            current = conn.execute(
                text('SELECT accuracy FROM run_history WHERE "isActive" = true ORDER BY date DESC LIMIT 1')
            ).fetchone()
        current_accuracy = current[0] if current else 0.0
        is_active = accuracy > current_accuracy

        # Deactivate old model if new one wins
        if is_active:
            with engine.begin() as conn:
                conn.execute(text('UPDATE run_history SET "isActive" = false WHERE "isActive" = true'))

        # Insert new run
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO run_history
                        (id, date, duration, accuracy, "datasetSize", success, "modelPath", "isActive", version)
                    VALUES
                        (:id, :date, :duration, :accuracy, :dataset_size, :success, :model_path, :is_active, :version)
                """),
                {
                    "id":           str(uuid.uuid4()),
                    "date":         datetime.now(),
                    "duration":     str(duration),
                    "accuracy":     accuracy,
                    "dataset_size": dataset_size,
                    "success":      True,
                    "model_path":   s3_uri,
                    "is_active":    is_active,
                    "version":      version,
                }
            )

        print(f"   run_history saved | is_active={is_active}")

        # Hot-swap in-memory model
        if is_active:
            requests.post("http://localhost:8001/reload-model", timeout=10)
            print("   In-memory model reloaded")

        print(f"Retraining complete -- version {version}\n")

    except Exception as e:
        duration = datetime.now() - start
        print(f"Retraining failed: {e}")
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO run_history
                        (id, date, duration, accuracy, "datasetSize", success, version)
                    VALUES
                        (:id, :date, :duration, :accuracy, :dataset_size, :success, :version)
                """),
                {
                    "id":           str(uuid.uuid4()),
                    "date":         datetime.now(),
                    "duration":     str(duration),
                    "accuracy":     0.0,
                    "dataset_size": 0,
                    "success":      False,
                    "version":      version,
                }
            )
