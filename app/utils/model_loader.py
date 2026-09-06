import os
import joblib
import requests
from app.db.mongo import get_model_registry


MODEL_BASE_URL = os.getenv("MODEL_BASE_URL", "")
LOCAL_MODEL_ROOT = "models"


def _ensure_model_local(model_path: str) -> str:
    """
    Ensure model exists locally.
    If missing → download from storage.
    """

    local_path = os.path.join(LOCAL_MODEL_ROOT, model_path)

    # already exists
    if os.path.exists(local_path):
        return local_path

    if not MODEL_BASE_URL:
        raise RuntimeError(
            f"Model missing locally and MODEL_BASE_URL not set: {model_path}"
        )

    # create folder
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    # download
    url = f"{MODEL_BASE_URL}/{model_path}"
    print(f"⬇️ Downloading model from {url}")

    r = requests.get(url, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to download model: {url}")

    with open(local_path, "wb") as f:
        f.write(r.content)

    print(f"✅ Model saved → {local_path}")
    return local_path


def load_production_model(horizon: int):

    registry = get_model_registry()

    model_doc = registry.find_one(
        {"horizon": horizon, "is_best": True}
    )

    if not model_doc:
        raise RuntimeError("No production model found")

    model_path = model_doc["model_path"]

    print(f"🚀 Loading production model: {model_doc['model_name']}")
    print(f"📁 Registry path: {model_path}")

    local_path = _ensure_model_local(model_path)

    model = joblib.load(local_path)

    return model, model_doc["features"]
