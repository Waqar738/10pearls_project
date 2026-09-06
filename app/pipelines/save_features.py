from datetime import datetime
from app.db.mongo import get_feature_store   # 🔥 THIS IMPORT WAS MISSING


def save_features(city: str, row: dict):
    collection = get_feature_store()

    doc = {
        "city": city,
        "datetime": row.get("datetime"),
        "aqi": row.get("aqi"),
        **row,
        "created_at": datetime.utcnow()
    }

    result = collection.insert_one(doc)
    print("Inserted ID:", result.inserted_id)
