import pandas as pd
import numpy as np
from app.db.mongo import get_database
from app.pipelines.feature_engineering_time import add_time_features
from app.pipelines.feature_engineering_lag import add_lag_features
from app.pipelines.feature_engineering_rolling import add_rolling_features


# -------------------------------------------------------
# Load Historical Data
# -------------------------------------------------------
def load_historical_df():

    collection = get_database()["historical_hourly_data"]
    data = list(collection.find({}, {"_id": 0}))

    if not data:
        raise RuntimeError("Historical data empty")

    return pd.DataFrame(data)


# -------------------------------------------------------
# Build Training Dataset
# -------------------------------------------------------
def build_training_dataset():
    """
    Build training dataset from historical_hourly_data
    Create lag + rolling + multi-horizon targets
    """

    db = get_database()

    collection = db["historical_hourly_data"]

    data = list(collection.find({}, {"_id": 0}))

    if not data:
        raise RuntimeError("❌ No historical data found")

    df = pd.DataFrame(data)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    # Target variable
    df["aqi_pm25"] = df["pm2_5"]

    # --------------------------
    # Time Features
    # --------------------------
    df["hour"] = df["datetime"].dt.hour
    df["day"] = df["datetime"].dt.day
    df["month"] = df["datetime"].dt.month

    # --------------------------
    # Lag Features
    # --------------------------
    df["lag_1"] = df["aqi_pm25"].shift(1)
    df["lag_3"] = df["aqi_pm25"].shift(3)
    df["lag_6"] = df["aqi_pm25"].shift(6)

    # --------------------------
    # Rolling Features
    # --------------------------
    df["roll_mean_6"] = df["aqi_pm25"].rolling(6).mean()
    df["roll_mean_12"] = df["aqi_pm25"].rolling(12).mean()

    # --------------------------
    # Multi-Horizon Targets
    # --------------------------
    df["target_h1"] = df["aqi_pm25"].shift(-24)
    df["target_h2"] = df["aqi_pm25"].shift(-48)
    df["target_h3"] = df["aqi_pm25"].shift(-72)

    df = df.dropna().reset_index(drop=True)

    print("✅ Training dataset built:", df.shape)

    return df