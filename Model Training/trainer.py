"""
Retraining script -- runs as a FastAPI background task.

Flow:
  1. Pull training_data from PostgreSQL
  2. Validate dataset (null checks on critical columns)
  3. Train LightGBM with 24 features (derived from 21 original columns)
  4. Evaluate on 20% test split (R² + RMSE)
  5. Save .pkl to /tmp -> upload to MinIO -> delete /tmp
  6. INSERT into run_history (is_active=True if beats current)
  7. POST /reload-model -> hot-swap in-memory model
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
from sklearn.metrics import r2_score, mean_squared_error
from sqlalchemy import create_engine, text

from storage import upload_model
import training_state as state

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hpa:hpa@localhost:5432/hpa")
NULL_FRACTION_ABORT_THRESHOLD = 0.30  # abort if >30% of rows have NULL in critical cols

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
CRITICAL_RAW_COLS = ["price", "bedrooms", "bathrooms", "sqft_living", "house_age", "zipcode"]


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


def _validate_dataset(df: pd.DataFrame) -> None:
    """Raises ValueError if too many rows are unusable."""
    total = len(df)
    if total == 0:
        raise ValueError("Dataset is empty.")

    state.push_log(f"Loaded {total} records from dataset...")
    state.push_log("Validating dataset (null checks, schema)...")

    null_counts = {col: int(df[col].isnull().sum()) for col in CRITICAL_RAW_COLS if col in df.columns}
    bad_total = sum(null_counts.values())
    if bad_total:
        worst = max(null_counts.items(), key=lambda kv: kv[1])
        state.push_log(f"  Found {bad_total} null values across critical columns (worst: {worst[0]}={worst[1]})")

    bad_rows = df[CRITICAL_RAW_COLS].isnull().any(axis=1).sum()
    fraction = bad_rows / total if total else 1.0
    if fraction > NULL_FRACTION_ABORT_THRESHOLD:
        raise ValueError(
            f"Too many invalid rows: {bad_rows}/{total} ({fraction:.0%}) exceed "
            f"the {NULL_FRACTION_ABORT_THRESHOLD:.0%} threshold."
        )


def _record_run(engine, *, run_id, start, duration, accuracy, rmse, dataset_size,
                success, model_path, is_active, version, error_message=None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO run_history
                    (id, date, duration, accuracy, rmse, "datasetSize",
                     success, "modelPath", "isActive", version, error_message)
                VALUES
                    (:id, :date, :duration, :accuracy, :rmse, :dataset_size,
                     :success, :model_path, :is_active, :version, :error_message)
            """),
            {
                "id":            run_id,
                "date":          datetime.now(),
                "duration":      str(duration),
                "accuracy":      accuracy,
                "rmse":          rmse,
                "dataset_size":  dataset_size,
                "success":       success,
                "model_path":    model_path,
                "is_active":     is_active,
                "version":       version,
                "error_message": error_message,
            }
        )


def _make_log_callback():
    """LightGBM callback that mirrors training iterations into training_state.

    Robust against any version-specific differences in CallbackEnv shape —
    falls back gracefully if attributes are missing.
    """
    def _cb(env):
        try:
            total = getattr(env, "end_iteration", 500)
            iteration = getattr(env, "iteration", 0)
            step = max(1, total // 10)
            if iteration == 0 or (iteration + 1) % step == 0 or iteration + 1 == total:
                eval_list = getattr(env, "evaluation_result_list", None) or []
                loss = eval_list[0][2] if eval_list else None
                loss_part = f" — l2: {loss:.4f}" if loss is not None else ""
                state.push_log(f"Iter {iteration + 1}/{total}{loss_part}")
                progress = 10 + int(80 * (iteration + 1) / total)
                state.set_progress(progress)
        except Exception as e:
            # Never let a logging callback break training
            state.push_log(f"⚠ log callback error: {e}")
    _cb.order = 30
    return _cb


def run_retrain():
    start = datetime.now()
    version = start.strftime("%Y%m%d_%H%M%S")
    run_id = str(uuid.uuid4())

    state.start(run_id)
    state.push_log(f"Training version {version}")

    engine = create_engine(DATABASE_URL)

    try:
        state.set_progress(2)
        df = _load_training_data(engine)
        state.set_progress(5)

        _validate_dataset(df)
        df = df.dropna(subset=FEATURE_COLS + [TARGET_COL])
        dataset_size = len(df)
        state.push_log(f"Dataset valid: {dataset_size} usable rows")
        state.set_progress(8)

        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        state.push_log("Encoding features, normalizing numerics...")
        state.set_progress(10)

        state.push_log("Training LightGBM regression model...")
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
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            eval_metric="l2",
            callbacks=[_make_log_callback()],
        )

        state.set_progress(92)
        state.push_log("Running evaluation on test split (20%)...")
        y_pred = model.predict(X_test)
        accuracy = float(r2_score(y_test, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        duration = datetime.now() - start
        state.push_log(f"R² = {accuracy:.4f} | RMSE = {rmse:,.0f} | duration: {duration}")
        state.set_progress(95)

        # Save to /tmp then upload to MinIO
        tmp_path = f"/tmp/lgbm_{version}.pkl"
        joblib.dump(model, tmp_path)
        s3_uri = upload_model(tmp_path, f"models/lgbm_{version}.pkl")
        os.remove(tmp_path)
        state.push_log(f"Uploaded to {s3_uri}")
        state.set_progress(98)

        # Check if this beats the current active model
        with engine.connect() as conn:
            current = conn.execute(
                text('SELECT accuracy FROM run_history WHERE "isActive" = true ORDER BY date DESC LIMIT 1')
            ).fetchone()
        current_accuracy = current[0] if current else 0.0
        is_active = accuracy > current_accuracy

        if is_active:
            with engine.begin() as conn:
                conn.execute(text('UPDATE run_history SET "isActive" = false WHERE "isActive" = true'))

        _record_run(
            engine,
            run_id=run_id, start=start, duration=duration,
            accuracy=accuracy, rmse=rmse, dataset_size=dataset_size,
            success=True, model_path=s3_uri, is_active=is_active, version=version,
        )

        if is_active:
            state.push_log("New model wins — marked Active.")
            try:
                requests.post("http://localhost:8001/reload-model", timeout=10)
                state.push_log("In-memory model reloaded.")
            except Exception as e:
                state.push_log(f"⚠ Reload-model failed (model still saved): {e}")
        else:
            state.push_log(f"Previous model kept (R² {current_accuracy:.4f} ≥ new {accuracy:.4f}).")

        state.complete()

    except Exception as e:
        duration = datetime.now() - start
        msg = str(e)
        try:
            _record_run(
                engine,
                run_id=run_id, start=start, duration=duration,
                accuracy=0.0, rmse=None, dataset_size=0,
                success=False, model_path="", is_active=False, version=version,
                error_message=msg,
            )
        except Exception as inner:
            state.push_log(f"⚠ Could not insert failed run row: {inner}")
        state.fail(msg)
