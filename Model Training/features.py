"""
Transforms PredictionRequest into the numpy feature vector the RF expects.
Column order must match FEATURE_NAMES in model_loader.py and FEATURE_COLS in trainer.py.
"""
import numpy as np
from datetime import datetime

CURRENT_YEAR = datetime.now().year


def build_feature_vector(req) -> np.ndarray:
    house_age = CURRENT_YEAR - req.year_built
    sqft_living = req.floor_area * 10.764   # UI sends m², model trained on sqft
    bedrooms = req.bedrooms
    bathrooms = req.bathrooms
    floors = max(req.floor_number or 1, 1)  # number of floors (min 1)

    # Parse zipcode from location if numeric, else default to central Seattle
    try:
        zipcode = int(str(req.location).strip()[:5])
        if not (90000 <= zipcode <= 99999):
            zipcode = 98103
    except (ValueError, TypeError):
        zipcode = 98103

    # Defaults for missing features
    sqft_lot = 5000
    view = 0
    grade = 7
    sqft_above = sqft_living
    sqft_basement = 0
    lat = 47.6062
    long = -122.3321
    sqft_living15 = sqft_living
    sqft_lot15 = 5000
    renovated = 0
    years_since_renovation = house_age
    total_sqft = sqft_living
    has_basement = 0
    price_per_sqft_area = sqft_living / (sqft_lot + 1)
    bath_per_bed = bathrooms / (bedrooms + 1)
    living_lot_ratio = sqft_living / (sqft_lot + 1)
    condition_enc = 3
    waterfront_enc = 0

    features = [
        bedrooms,
        bathrooms,
        sqft_living,
        sqft_lot,
        floors,
        view,
        grade,
        sqft_above,
        sqft_basement,
        zipcode,
        lat,
        long,
        sqft_living15,
        sqft_lot15,
        house_age,
        renovated,
        years_since_renovation,
        total_sqft,
        has_basement,
        price_per_sqft_area,
        bath_per_bed,
        living_lot_ratio,
        condition_enc,
        waterfront_enc,
    ]
    return np.array([features], dtype=float)  # shape (1, 24)


def build_price_factors(req, importances: np.ndarray, feature_names: list) -> dict:
    """Glass Box dict shown in [Results] Vizualizare Rezultate."""
    labels = {
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "sqft_living": "Floor area",
        "sqft_lot": "Lot size",
        "floors": "Floor number",
        "view": "View",
        "grade": "Grade",
        "sqft_above": "Above ground area",
        "sqft_basement": "Basement area",
        "zipcode": "Zipcode",
        "lat": "Latitude",
        "long": "Longitude",
        "sqft_living15": "Living area of 15 neighbors",
        "sqft_lot15": "Lot size of 15 neighbors",
        "house_age": "Age of property",
        "renovated": "Renovated",
        "years_since_renovation": "Years since renovation",
        "total_sqft": "Total square footage",
        "has_basement": "Has basement",
        "price_per_sqft_area": "Price per sqft area",
        "bath_per_bed": "Bathrooms per bedroom",
        "living_lot_ratio": "Living to lot ratio",
        "condition_enc": "Condition",
        "waterfront_enc": "Waterfront",
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
