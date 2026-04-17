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
    "sqft_living",      # floor_area from the form
    "bedrooms",
    "bathrooms",
    "floors",           # floor_number from the form
    "house_age",        # derived: current_year - year_built
    "property_type",    # encoded: Apartment=0, House=1, Villa=2
    "has_parking",
    "has_pool",
    "has_balcony",
    "has_elevator",
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
        print("⚠️  No active model in DB — waiting for first retrain.")
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
