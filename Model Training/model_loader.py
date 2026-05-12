"""
Singleton model loader.
Loads the active model from MinIO once at startup.
Hot-swaps on POST /reload-model after each retrain.
"""
import os
import joblib
from sqlalchemy import create_engine, text

from storage import download_model_to_buffer

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://hpa:hpa@localhost:5432/hpa")

# Column order MUST match trainer.py FEATURE_COLS
FEATURE_NAMES = [
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

_model = None
_model_meta = {}


def _get_active_row():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                'SELECT "modelPath", version, accuracy, "datasetSize" '
                'FROM run_history WHERE "isActive" = true '
                'ORDER BY date DESC LIMIT 1'
            )
        ).fetchone()
    return row


def load_active_model():
    global _model, _model_meta

    row = _get_active_row()
    if not row:
        print("No active model in DB — waiting for first retrain.")
        return

    model_path, version, accuracy, dataset_size = row
    print(f"Loading model: {model_path}")

    buffer = download_model_to_buffer(model_path)
    _model = joblib.load(buffer)
    _model_meta = {
        "version":      version,
        "accuracy":     accuracy,
        "dataset_size": dataset_size,
        "model_path":   model_path,
    }
    print(f"✅ Model ready | version={version} | accuracy={accuracy:.4f}")


def get_model():
    if _model is None:
        load_active_model()
    if _model is None:
        raise RuntimeError("Niciun model disponibil. Antrenați modelul din panoul admin.")
    return _model


def get_meta() -> dict:
    return _model_meta


def get_feature_names() -> list:
    return FEATURE_NAMES
