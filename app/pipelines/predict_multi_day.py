"""
Multi-Day Rolling Forecast
Generates recursive N-day forecast using production model
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.db.mongo import get_db
from app.pipelines.load_production_model import load_production_model


def generate_multi_day_forecast(horizon: int = 3):

    db = get_db()

    # 1️⃣ Load correct horizon model
    model, features, model_version = load_production_model(horizon=horizon)

    # 2️⃣ Get latest feature row
    latest_doc = list(
        db["feature_store"]
        .find()
        .sort("datetime", -1)
        .limit(1)
    )

    if not latest_doc:
        raise RuntimeError("No feature data found")

    latest_doc = latest_doc[0]

    current_features = {
        col: latest_doc.get(col, 0)
        for col in features
    }

    predictions = []

    base_time = datetime.utcnow()

    # 3️⃣ Rolling forecast
    for step in range(1, horizon + 1):

        X = pd.DataFrame([current_features])

        # Model predicts log(AQI)
        log_pred = float(model.predict(X)[0])

        # Inverse transform
        pred = float(np.expm1(log_pred))

        future_datetime = base_time + timedelta(days=step)

        predictions.append({
            "datetime": future_datetime,
            "predicted_aqi": pred
        })

        # 4️⃣ Shift lag features safely
        lag_cols = [col for col in features if "_lag_" in col]

        if lag_cols:
            lag_cols_sorted = sorted(
                lag_cols,
                key=lambda x: int(x.split("_")[-1]),
                reverse=True
            )

            for i in range(len(lag_cols_sorted) - 1):
                current_features[lag_cols_sorted[i]] = current_features[lag_cols_sorted[i + 1]]

            smallest_lag = sorted(
                lag_cols,
                key=lambda x: int(x.split("_")[-1])
            )[0]

            current_features[smallest_lag] = pred

    forecast_doc = {
        "horizon": horizon,
        "generated_at": base_time,
        "model_version": model_version,
        "predictions": predictions
    }

    db["daily_forecast"].insert_one(forecast_doc)

    return forecast_doc
