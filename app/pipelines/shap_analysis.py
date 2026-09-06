import shap
import pandas as pd
import numpy as np
from datetime import datetime

from app.db.mongo import get_db, get_model_registry   # 🔥 ADD THIS
from app.pipelines.load_production_model import load_production_model
from pathlib import Path
import joblib   # ✅ ADD THIS





# ==========================================================
# SHAP ANALYSIS (Production Only)
# ==========================================================
def generate_shap_analysis():

    db = get_db()
    registry = get_model_registry()

    # ------------------------------------------------------
    # 1️⃣ Load Production Model (horizon=1)
    # ------------------------------------------------------
    model_doc = registry.find_one({
        "horizon": 1,
        "is_best": True
    })

    if not model_doc:
        raise RuntimeError("No production model found for SHAP")

    model_path = Path(model_doc["model_path"])

    if not model_path.exists():
        raise RuntimeError(f"Model file not found: {model_path}")

    model = joblib.load(model_path)

    features = model_doc["features"]

    # ------------------------------------------------------
    # 2️⃣ Get Latest Feature Row
    # ------------------------------------------------------
    latest_doc = list(
        db["feature_store"]
        .find()
        .sort("datetime", -1)
        .limit(1)
    )

    if not latest_doc:
        raise RuntimeError("No feature data available")

    latest_doc = latest_doc[0]

    X = pd.DataFrame([{
        col: latest_doc.get(col)
        for col in features
    }])

    X = X.fillna(0)

    # ------------------------------------------------------
    # 3️⃣ Prediction
    # ------------------------------------------------------
    prediction = float(model.predict(X)[0])
    pred_log = model.predict(X)[0]
    prediction = float(np.expm1(pred_log))


    # ------------------------------------------------------
    # 4️⃣ SHAP (Tree models only)
    # ------------------------------------------------------
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

    except Exception:
        raise RuntimeError(
            "SHAP only supported for tree-based models (RF, XGB, GB)"
        )

    contributions = []

    for feature, value in zip(features, shap_values[0]):
        contributions.append({
            "feature": feature,
            "shap_value": float(value)
        })

    # Sort by importance
    contributions = sorted(
        contributions,
        key=lambda x: abs(x["shap_value"]),
        reverse=True
    )

    return {
        "status": "success",
        "model_name": model_doc["model_name"],
        "prediction": prediction,
        "generated_at": datetime.utcnow().isoformat(),
        "contributions": contributions
    }
