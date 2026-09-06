import os
from datetime import datetime
from pymongo import MongoClient

# -----------------------------
# Load Environment Variables
# -----------------------------
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "aqi_system")

if not MONGODB_URI:
    raise ValueError("❌ MONGODB_URI not found in environment variables")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]
registry = db["model_registry"]

# -----------------------------
# Define Feature List
# -----------------------------
features = [
    "pm10", "carbon_monoxide", "nitrogen_dioxide",
    "sulphur_dioxide", "ozone",
    "hour", "day_of_week", "day_of_month",
    "month", "week_of_year",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "pm2_5_lag_1", "pm2_5_lag_6", "pm2_5_lag_12",
    "pm2_5_lag_24", "pm2_5_lag_48",
    "pm2_5_lag_72", "pm2_5_lag_168",
    "pm2_5_roll_mean_6", "pm2_5_roll_std_6",
    "pm2_5_roll_mean_12", "pm2_5_roll_std_12",
    "pm2_5_roll_mean_24", "pm2_5_roll_std_24",
    "pm2_5_roll_mean_48"
]

# -----------------------------
# Clear Previous Production Flags
# -----------------------------
registry.update_many(
    {"status": "production"},
    {"$set": {"is_best": False}}
)

# -----------------------------
# Register Models
# -----------------------------
models = [
    {
        "model_name": "random_forest",
        "horizon": 1,
        "model_path": "models/rf_h1/model.joblib",
        "model_version": "rf_h1_v1"
    },
    {
        "model_name": "random_forest",
        "horizon": 3,
        "model_path": "models/rf_h3/model.joblib",
        "model_version": "rf_h3_v1"
    },
    {
        "model_name": "random_forest",
        "horizon": 5,
        "model_path": "models/rf_h5/model.joblib",
        "model_version": "rf_h5_v1"
    }
]

for model in models:
    doc = {
        "model_name": model["model_name"],
        "horizon": model["horizon"],
        "status": "production",
        "is_best": True,
        "model_path": model["model_path"],
        "features": features,
        "model_version": model["model_version"],
        "registered_at": datetime.utcnow()
    }

    registry.update_one(
        {
            "model_name": model["model_name"],
            "horizon": model["horizon"]
        },
        {"$set": doc},
        upsert=True
    )

    print(f"✅ Registered model for horizon {model['horizon']}")

print("\n🚀 Production models successfully registered.")
model_doc = {
    "horizon": horizon,
    "model_path": f"models/rf_h{horizon}/{model_filename}",
    "features": feature_list,
    "is_best": True
}

