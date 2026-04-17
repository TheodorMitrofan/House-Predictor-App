"""
Retraining script — runs as a FastAPI background task.

Flow:
  1. Pull training_data from PostgreSQL
  2. Train Random Forest
  3. Evaluate on 20% test split
  4. Save .pkl to /tmp → upload to MinIO → delete /tmp
  5. INSERT into run_history (is_active=True if beats current)
  6. POST /reload-model → hot-swap in-memory model
"""
import os
import uuid
import joblib
import requests
import numpy as np
import pandas as pd

from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sqlalchemy import create_engine, text

from storage import upload_model

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hpa:hpa@localhost:5432/hpa")

# Must match FEATURE_NAMES in model_loader.py
FEATURE_COLS = [
    "sqft_living",
    "bedrooms",
    "bathrooms",
    "floors",
    "house_age",
    "property_type_enc",
    "has_parking",
    "has_pool",
    "has_balcony",
    "has_elevator",
]
TARGET_COL = "price"


def _load_training_data(engine) -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM training_data", engine)

    # Derived features
    df["house_age"] = datetime.now().year - df["yr_built"]

    # Boolean feature columns not present in Kaggle dataset — default 0
    for col in ["has_parking", "has_pool", "has_balcony", "has_elevator"]:
        if col not in df.columns:
            df[col] = 0

    # property_type not in Kaggle dataset — default to House (1)
    # Will be correct once users add entries manually via the admin panel
    if "property_type_enc" not in df.columns:
        df["property_type_enc"] = 1

    return df


def run_retrain():
    start = datetime.now()
    version = start.strftime("%Y%m%d_%H%M%S")
    print(f"\n🔄 Retraining started — version {version}")

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

        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            n_jobs=-1,
            random_state=42,
        )
        model.fit(X_train, y_train)

        accuracy = float(r2_score(y_test, model.predict(X_test)))
        duration = datetime.now() - start
        print(f"   R² accuracy: {accuracy:.4f} | duration: {duration}")

        # Save to /tmp then upload to MinIO
        tmp_path = f"/tmp/rf_{version}.pkl"
        joblib.dump(model, tmp_path)
        s3_uri = upload_model(tmp_path, f"models/rf_{version}.pkl")
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
            print("   In-memory model reloaded ✅")

        print(f"✅ Retraining complete — version {version}\n")

    except Exception as e:
        duration = datetime.now() - start
        print(f"❌ Retraining failed: {e}")
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
