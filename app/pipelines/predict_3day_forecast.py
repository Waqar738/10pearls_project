import pandas as pd
import joblib
import numpy as np
from datetime import datetime, timedelta
from app.db.mongo import get_database
from app.pipelines.load_production_model import load_production_model


def predict_3day_forecast():
    """
    Generate 3-day (72-hour) AQI forecast using production models
    """
    
    print("🔮 Generating 3-day AQI forecast...")
    
    # Get the latest data point for feature engineering
    db = get_database()
    collection = db["historical_hourly_data"]
    
    # Get the most recent records (need enough for lag features)
    records = list(collection.find(
        {}, 
        {"_id": 0}
    ).sort("datetime", -1).limit(200))
    
    if not records:
        raise RuntimeError("No historical data found")
    
    # Create DataFrame with all records
    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    
    # Use the latest record for prediction
    latest = df.iloc[-1:].copy()
    
    # Create the same features as training
    # 1. Target variable
    latest["aqi_pm25"] = latest["pm2_5"]
    
    # 2. Time features
    latest["hour"] = latest["datetime"].dt.hour
    latest["day"] = latest["datetime"].dt.day
    latest["month"] = latest["datetime"].dt.month
    
    # 3. Lag features (using historical data)
    df["aqi_pm25"] = df["pm2_5"]
    df["lag_1"] = df["aqi_pm25"].shift(1)
    df["lag_3"] = df["aqi_pm25"].shift(3)
    df["lag_6"] = df["aqi_pm25"].shift(6)
    
    # Get the latest lag values
    latest_lag = df.iloc[-1:][["lag_1", "lag_3", "lag_6"]].copy()
    
    # 4. Rolling features
    df["roll_mean_6"] = df["aqi_pm25"].rolling(6).mean()
    df["roll_mean_12"] = df["aqi_pm25"].rolling(12).mean()
    
    latest_roll = df.iloc[-1:][["roll_mean_6", "roll_mean_12"]].copy()
    
    # ============================================================
    # FIX: Remove duplicate columns and combine correctly
    # ============================================================
    
    # Start with the base latest data
    combined = latest.copy()
    
    # Add lag features (only if they don't already exist)
    for col in ["lag_1", "lag_3", "lag_6"]:
        if col not in combined.columns:
            combined[col] = latest_lag[col].values[0]
    
    # Add rolling features
    for col in ["roll_mean_6", "roll_mean_12"]:
        if col not in combined.columns:
            combined[col] = latest_roll[col].values[0]
    
    # ============================================================
    # EXACT FEATURE ORDER FROM TRAINING
    # ============================================================
    feature_cols = [
        'pm2_5', 'pm10', 'carbon_monoxide', 'nitrogen_dioxide', 
        'sulphur_dioxide', 'ozone', 'aqi_pm25', 'hour', 'day', 'month',
        'lag_1', 'lag_3', 'lag_6', 'roll_mean_6', 'roll_mean_12'
    ]
    
    # Check if all features exist
    missing = [col for col in feature_cols if col not in combined.columns]
    if missing:
        print(f"⚠️ Missing features: {missing}")
        for col in missing:
            combined[col] = 0
    
    # Select features in the EXACT order
    X = combined[feature_cols]
    
    print(f"📊 Feature shape: {X.shape}")
    print(f"📋 Features: {list(X.columns)}")
    
    # Get production models for each horizon
    forecasts = []
    
    for horizon in [1, 2, 3]:
        print(f"  Predicting horizon {horizon}...")
        
        try:
            # Load model for this horizon
            model = load_production_model(horizon)
            
            if model is None:
                print(f"    ⚠️ No model found for horizon {horizon}")
                continue
            
            # Make prediction
            pred = model.predict(X)[0]
            
            # Calculate date
            forecast_date = datetime.now() + timedelta(days=horizon)
            
            forecasts.append({
                "horizon": horizon,
                "date": forecast_date.strftime("%Y-%m-%d"),
                "value": float(pred)
            })
            
            print(f"    ✅ Day {horizon}: {float(pred):.2f}")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Save forecast to database
    if forecasts:
        forecast_collection = db["forecast_results"]
        forecast_collection.delete_many({})  # Clear old forecasts
        
        for forecast in forecasts:
            forecast["created_at"] = datetime.utcnow()
            forecast_collection.insert_one(forecast)
        
        print("✅ 3-day forecast saved to MongoDB")
    else:
        print("❌ No forecasts generated")
    
    return forecasts


if __name__ == "__main__":
    predictions = predict_3day_forecast()
    
    if predictions:
        print("\n" + "="*50)
        print("📊 3-DAY AQI FORECAST")
        print("="*50)
        for p in predictions:
            print(f"  Day {p['horizon']} ({p['date']}): {p['value']:.2f}")
        print("="*50)
    else:
        print("❌ No predictions generated")