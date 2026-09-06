import joblib
from gridfs import GridFS
from app.db.mongo import get_db, get_model_registry

db = get_db()
registry = get_model_registry()
fs = GridFS(db)

# Get production model (H1)
model_doc = registry.find_one({
    "horizon": 1,
    "is_best": True
})

if not model_doc:
    raise RuntimeError("No production model found")

gridfs_id = model_doc["gridfs_id"]

# Download model bytes
model_bytes = fs.get(gridfs_id).read()

with open("production_model_h1.pkl", "wb") as f:
    f.write(model_bytes)

print("✅ Model exported as production_model_h1.pkl")