"""
Feature Engineering
-------------------
- Reads historical_hourly_data
- Creates lag features
- Creates rolling features
- Creates multi-horizon targets
- Saves to feature_store
"""

import pandas as pd
from app.db.mongo import get_feature_store, get_db


def generate_features():
    print("🔄 Generating features...")

    db = get_db()

    # -------------------------------------------------
    # 1️⃣ Load historical data
    # -------------------------------------------------
    data = list(db["historical_hourly_data"].find({}, {"_id": 0}))

    if not data:
        raise RuntimeError("❌ No historical data found")

    df = pd.DataFrame(data)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    # -------------------------------------------------
    # 2️⃣ Create Lag Features
    # -------------------------------------------------
    df["pm2_5_lag_1"] = df["pm2_5"].shift(1)
    df["pm2_5_lag_3"] = df["pm2_5"].shift(3)
    df["pm2_5_lag_6"] = df["pm2_5"].shift(6)
    df["pm2_5_lag_12"] = df["pm2_5"].shift(12)
    df["pm2_5_lag_24"] = df["pm2_5"].shift(24)

    # -------------------------------------------------
    # 3️⃣ Rolling Statistics
    # -------------------------------------------------
    df["pm2_5_roll_mean_6"] = df["pm2_5"].rolling(6).mean()
    df["pm2_5_roll_mean_12"] = df["pm2_5"].rolling(12).mean()
    df["pm2_5_roll_mean_24"] = df["pm2_5"].rolling(24).mean()

    # -------------------------------------------------
    # 4️⃣ Time Features
    # -------------------------------------------------
    df["hour"] = df["datetime"].dt.hour
    df["day_of_week"] = df["datetime"].dt.dayofweek

    # -------------------------------------------------
    # 5️⃣ Multi-Horizon Targets
    # -------------------------------------------------
    df["target_h1"] = df["pm2_5"].shift(-24)
    df["target_h2"] = df["pm2_5"].shift(-48)
    df["target_h3"] = df["pm2_5"].shift(-72)

    # -------------------------------------------------
    # 6️⃣ Drop NaNs
    # -------------------------------------------------
    df = df.dropna()

    # -------------------------------------------------
    # 7️⃣ Store in feature_store
    # -------------------------------------------------
    feature_store = get_feature_store()

    feature_store.delete_many({})  # overwrite safely

    feature_store.insert_many(df.to_dict("records"))

    print(f"✅ Stored {len(df)} feature rows")
