from pydantic import BaseModel, Field
from typing import Optional


class PredictionRequest(BaseModel):
    # Required — marked * in [Input] Introducere date predictie
    location:      str   = Field(..., min_length=2)
    property_type: str   = Field(..., pattern="^(Apartment|House|Villa)$")
    floor_area:    float = Field(..., gt=0)
    bedrooms:      int   = Field(..., ge=0)
    year_built:    int   = Field(..., ge=1800, le=2026)

    # Optional
    bathrooms:    Optional[int] = Field(default=0, ge=0)
    floor_number: Optional[int] = Field(default=0)

    # Feature toggles (pills in the UI)
    has_parking:  bool = False
    has_pool:     bool = False
    has_balcony:  bool = False
    has_elevator: bool = False


class PredictionResponse(BaseModel):
    predicted_price: int
    confidence:      float   # 0.0–1.0 → shown as % with green/yellow/red
    price_factors:   dict    # Glass Box section in [Results]
    explanation:     str     # AI Explanation narrative
    tips:            list    # [Advice] Sfaturi primite de la model
