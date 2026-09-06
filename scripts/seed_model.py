from pymongo import MongoClient
import os
from datetime import datetime

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set")

client = MongoClient(MONGO_URI)
db = client["aqi_system"]

db.model_registry.insert_one({
    "model_name": "baseline_dummy",
    "horizon": 1,
    "is_production": True,
    "metrics": {
        "rmse": 999
    },
    "created_at": datetime.utcnow()
})

print("✅ Production model seeded")
