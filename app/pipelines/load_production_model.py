import joblib
import io
from functools import lru_cache
from gridfs import GridFS

from app.db.mongo import get_model_registry, get_database


# ==================================================
# Load model from GridFS
# ==================================================
@lru_cache(maxsize=10)
def load_production_model(horizon: int):
    """
    Load production model for a given horizon from GridFS
    """
    
    registry = get_model_registry()

    model_doc = registry.find_one({
        "horizon": horizon,
        "status": "production",
        "is_best": True
    })

    if not model_doc:
        raise RuntimeError(
            f"No production model found for horizon={horizon}"
        )

    # Get GridFS ID
    gridfs_id = model_doc.get("gridfs_id")
    
    if not gridfs_id:
        raise RuntimeError("Model registry missing gridfs_id")

    # Load from GridFS
    db = get_database()
    fs = GridFS(db)
    
    try:
        gridfs_file = fs.get(gridfs_id)
        model_bytes = gridfs_file.read()
        model = joblib.load(io.BytesIO(model_bytes))
    except Exception as e:
        raise RuntimeError(f"Failed to load model from GridFS: {e}")

    # Get features
    features = model_doc.get("features")
    if not features:
        raise RuntimeError("Model registry missing features")

    model_version = model_doc.get(
        "model_version",
        f"{model_doc.get('model_name','model')}_h{horizon}"
    )

    return model