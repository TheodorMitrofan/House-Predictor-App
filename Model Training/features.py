"""
Transforms PredictionRequest into the numpy feature vector the RF expects.
Column order must match FEATURE_NAMES in model_loader.py and FEATURE_COLS in trainer.py.
"""
import numpy as np
from datetime import datetime

PROPERTY_TYPE_MAP = {"Apartment": 0, "House": 1, "Villa": 2}
CURRENT_YEAR = datetime.now().year


def build_feature_vector(req) -> np.ndarray:
    features = [
        req.floor_area,                               # sqft_living
        req.bedrooms,
        req.bathrooms,
        req.floor_number,                             # floors
        CURRENT_YEAR - req.year_built,                # house_age
        PROPERTY_TYPE_MAP.get(req.property_type, 1),  # property_type encoded
        int(req.has_parking),
        int(req.has_pool),
        int(req.has_balcony),
        int(req.has_elevator),
    ]
    return np.array([features], dtype=float)  # shape (1, 10)


def build_price_factors(req, importances: np.ndarray, feature_names: list) -> dict:
    """Glass Box dict shown in [Results] Vizualizare Rezultate."""
    labels = {
        "sqft_living":   "Floor area",
        "bedrooms":      "Bedrooms",
        "bathrooms":     "Bathrooms",
        "floors":        "Floor number",
        "house_age":     "Age of property",
        "property_type": "Property type",
        "has_parking":   "Parking garage",
        "has_pool":      "Swimming pool",
        "has_balcony":   "Balcony / Terrace",
        "has_elevator":  "Elevator",
    }
    return {
        labels.get(name, name): round(float(imp) * 100, 2)
        for name, imp in zip(feature_names, importances)
    }


def generate_tips(req, predicted_price: int) -> list:
    """
    Rule-based renovation tips for [Advice] Sfaturi primite de la model.
    Filtered by property type as per the spec.
    """
    tips = []

    if not req.has_parking:
        tips.append({
            "category":    "Parking",
            "action":      "Adaugă loc de parcare",
            "cost_min":    5000,
            "cost_max":    15000,
            "value_added": int(predicted_price * 0.04),
        })

    if not req.has_balcony and req.property_type == "Apartment":
        tips.append({
            "category":    "Exterior",
            "action":      "Amenajare balcon / terasă",
            "cost_min":    2000,
            "cost_max":    8000,
            "value_added": int(predicted_price * 0.02),
        })

    if not req.has_pool and req.property_type in ("House", "Villa"):
        tips.append({
            "category":    "Exterior",
            "action":      "Instalare piscină",
            "cost_min":    20000,
            "cost_max":    60000,
            "value_added": int(predicted_price * 0.07),
        })

    if req.year_built < 2010:
        tips.append({
            "category":    "Smart Home",
            "action":      "Sistem smart home (iluminat automatizat, termostat inteligent)",
            "cost_min":    3000,
            "cost_max":    10000,
            "value_added": int(predicted_price * 0.03),
        })

    return tips
