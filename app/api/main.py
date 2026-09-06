from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import joblib
import io
from gridfs import GridFS
import pandas as pd
from bson import ObjectId

from app.db.mongo import (
    get_database,
    get_model_registry,
    get_feature_store
)

app = FastAPI(title="Karachi AQI Backend")

# ======================================================
# HEALTH
# ======================================================

@app.get("/health")
@app.head("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "AQI Backend Running"
    }

# ======================================================
# GLOBAL MODEL CACHE (LAZY LOAD ONLY)
# ======================================================

models_cache = {}

# ======================================================
# LOAD PRODUCTION MODEL FROM GRIDFS
# ======================================================

def load_production_model(horizon: int):

    registry = get_model_registry()
    db = get_database()
    fs = GridFS(db)

    doc = registry.find_one({
        "horizon": horizon,
        "is_best": True
    })

    if not doc:
        raise HTTPException(status_code=404, detail="No production model found")

    if "gridfs_id" not in doc:
        raise HTTPException(status_code=500, detail="Model missing gridfs_id")

    model_bytes = fs.get(doc["gridfs_id"]).read()
    model = joblib.load(io.BytesIO(model_bytes))

    return model, doc["features"], doc

# ======================================================
# GET LATEST FEATURE ROW
# ======================================================

def get_latest_feature_row(feature_columns):

    feature_store = get_feature_store()

    latest_doc = feature_store.find_one(
        sort=[("datetime", -1)]
    )

    if not latest_doc:
        raise HTTPException(
            status_code=500,
            detail="Feature store empty. Run training first."
        )

    row_dict = {}

    for col in feature_columns:
        if col not in latest_doc:
            raise HTTPException(
                status_code=500,
                detail=f"Missing feature column: {col}"
            )
        row_dict[col] = latest_doc[col]

    return pd.DataFrame([row_dict])

# ======================================================
# FORECAST ENDPOINT
# ======================================================

@app.get("/forecast")
def forecast():

    results = {}

    for horizon in [1, 2, 3]:

        # Lazy load
        if horizon not in models_cache:
            model, features, _ = load_production_model(horizon)
            models_cache[horizon] = (model, features)

        model, features = models_cache[horizon]

        X = get_latest_feature_row(features)
        prediction = float(model.predict(X)[0])

        future_date = (
            datetime.utcnow() + timedelta(days=horizon)
        ).strftime("%Y-%m-%d")

        results[f"{horizon}_day"] = {
            "value": round(prediction, 2),
            "date": future_date
        }

    return results

# ======================================================
# BEST PRODUCTION MODEL
# ======================================================

@app.get("/models/best")
def best_model():

    registry = get_model_registry()

    doc = registry.find_one({"is_best": True})

    if not doc:
        return {
            "status": "error",
            "message": "No best model found"
        }

    # Convert ObjectId safely
    doc["_id"] = str(doc["_id"])

    if "gridfs_id" in doc:
        doc["gridfs_id"] = str(doc["gridfs_id"])

    return {
        "status": "success",
        "model": doc
    }

# ======================================================
# FEATURE IMPORTANCE
# ======================================================

@app.get("/features/importance")
def feature_importance(horizon: int = 1):

    # Lazy load model
    if horizon not in models_cache:
        model, features, _ = load_production_model(horizon)
        models_cache[horizon] = (model, features)

    model, features = models_cache[horizon]

    if not hasattr(model, "feature_importances_"):
        return {
            "status": "error",
            "message": "Model does not support feature importance"
        }

    data = [
        {
            "feature": f,
            "importance": float(i)
        }
        for f, i in zip(features, model.feature_importances_)
    ]

    return {
        "status": "success",
        "features": data
    }