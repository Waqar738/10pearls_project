import pandas as pd
from app.db.mongo import get_db


# ==========================================================
# 1️⃣ Load Historical Data
# ==========================================================
def load_historical_df():

    db = get_db()
    collection = db["historical_hourly_data"]

    data = list(collection.find({}, {"_id": 0}))

    if not data:
        raise RuntimeError("No historical data found in MongoDB")

    df = pd.DataFrame(data)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df


# ==========================================================
# 2️⃣ Feature Engineering (COMMON for training + inference)
# ==========================================================
def build_final_dataframe():
    """
    Build full feature dataframe.
    DO NOT drop NaN here.
    Used by feature pipeline + inference.
    """

    df = load_historical_df()

    # Target base
    df["aqi_pm25"] = df["pm2_5"]

    # Time Features
    df["hour"] = df["datetime"].dt.hour
    df["day"] = df["datetime"].dt.day
    df["month"] = df["datetime"].dt.month

    # Lag Features
    df["lag_1"] = df["aqi_pm25"].shift(1)
    df["lag_3"] = df["aqi_pm25"].shift(3)
    df["lag_6"] = df["aqi_pm25"].shift(6)

    # Rolling Features
    df["roll_mean_6"] = df["aqi_pm25"].rolling(6).mean()
    df["roll_mean_12"] = df["aqi_pm25"].rolling(12).mean()

    return df


# ==========================================================
# 3️⃣ Training Dataset Builder
# ==========================================================
def build_training_dataset(horizon: int):
    """
    Used ONLY for training.
    Creates horizon-specific target.
    """

    df = build_final_dataframe()

    # Multi-horizon targets
    df["target_h1"] = df["aqi_pm25"].shift(-24)
    df["target_h2"] = df["aqi_pm25"].shift(-48)
    df["target_h3"] = df["aqi_pm25"].shift(-72)

    print("Before dropna:", df.shape)

    df = df.dropna().reset_index(drop=True)

    print("After dropna:", df.shape)

    target_column = f"target_h{horizon}"

    if target_column not in df.columns:
        raise ValueError("Invalid horizon")

    y = df[target_column]

    X = df.drop(
        columns=[
            "datetime",
            "target_h1",
            "target_h2",
            "target_h3",
        ],
        errors="ignore"
    )

    return X, y
