from datetime import datetime
import json
from pathlib import Path


REGISTRY_PATH = Path("model_registry.json")


def register_model(
    model_name: str,
    horizon: int,
    rmse: float,
    r2: float,
    features: list,
    status: str = "inactive"
):
    """
    Register a trained model with metadata.
    """

    entry = {
        "model_name": model_name,
        "horizon_hours": horizon,
        "rmse": round(rmse, 2),
        "r2": round(r2, 3),
        "features": features,
        "status": status,
        "trained_at": datetime.utcnow().isoformat()
    }

    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text())
    else:
        registry = []

    registry.append(entry)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))

    print(f"✅ Registered {model_name} | +{horizon}h | status={status}")