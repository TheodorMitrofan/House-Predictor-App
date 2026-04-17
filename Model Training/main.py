"""
ProphetAI — FastAPI ML Service

Endpoints:
  POST /predict       — called by Django for each user prediction request
  POST /retrain       — called by Django admin panel, kicks off background train
  POST /reload-model  — called by trainer.py after retrain completes
  GET  /model-info    — feeds the admin Model Training stats card
  GET  /health        — liveness probe (Django pings this before forwarding requests)
"""
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, HTTPException

from schemas import PredictionRequest, PredictionResponse
from model_loader import load_active_model, get_model, get_meta, get_feature_names
from features import build_feature_vector, build_price_factors, generate_tips
from trainer import run_retrain


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_active_model()
    except Exception as e:
        print(f"⚠️  Startup model load failed: {e}")
    yield


app = FastAPI(title="ProphetAI ML Service", version="1.0.0", lifespan=lifespan)


# ── Prediction ────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    model = get_model()

    X = build_feature_vector(req)

    # Collect predictions from every tree for confidence calculation
    tree_preds = np.array([tree.predict(X)[0] for tree in model.estimators_])
    predicted_price = int(np.mean(tree_preds))

    # Confidence: how tightly the trees agree (1 - coefficient of variation)
    std = np.std(tree_preds)
    cv  = std / (predicted_price + 1e-9)
    confidence = round(float(np.clip(1 - cv, 0.0, 1.0)), 4)

    price_factors = build_price_factors(
        req, model.feature_importances_, get_feature_names()
    )

    top_factor = max(price_factors, key=price_factors.get)
    explanation = (
        f"Proprietatea de tip {req.property_type} cu o suprafață de {req.floor_area}m², "
        f"construită în {req.year_built}, situată în {req.location}, "
        f"a fost evaluată la ${predicted_price:,}. "
        f"Factorul cu cel mai mare impact a fost '{top_factor}'."
    )

    tips = generate_tips(req, predicted_price)

    return PredictionResponse(
        predicted_price=predicted_price,
        confidence=confidence,
        price_factors=price_factors,
        explanation=explanation,
        tips=tips,
    )


# ── Training ──────────────────────────────────────────────────────────

@app.post("/retrain")
def retrain(background_tasks: BackgroundTasks):
    """
    Returns immediately — training runs in the background.
    Angular shows a progress state while this is running.
    """
    background_tasks.add_task(run_retrain)
    return {"message": "Reantrenare pornită în background."}


@app.post("/reload-model")
def reload_model():
    """Hot-swap the in-memory model after trainer.py uploads a new .pkl to MinIO."""
    try:
        load_active_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Model reîncărcat cu succes.", "meta": get_meta()}


# ── Info / Health ─────────────────────────────────────────────────────

@app.get("/model-info")
def model_info():
    """Feeds the admin Model Training stats card (accuracy, version, dataset size)."""
    meta = get_meta()
    if not meta:
        raise HTTPException(status_code=404, detail="Niciun model activ.")
    model = get_model()
    return {
        **meta,
        "n_estimators": model.n_estimators,
        "features":     get_feature_names(),
    }


@app.get("/health")
def health():
    meta = get_meta()
    return {
        "status":       "ok",
        "model_loaded": meta.get("version") is not None,
        "version":      meta.get("version", "none"),
    }
