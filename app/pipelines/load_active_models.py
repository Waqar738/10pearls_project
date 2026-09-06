import json
from pathlib import Path


REGISTRY_PATH = Path("model_registry.json")


def load_active_models():
    """
    Load all ACTIVE models from the registry.
    Returns a dict keyed by horizon.
    """

    if not REGISTRY_PATH.exists():
        raise FileNotFoundError("model_registry.json not found")

    registry = json.loads(REGISTRY_PATH.read_text())

    active_models = {}

    for entry in registry:
        if entry["status"] == "active":
            horizon = entry["horizon_hours"]
            active_models[horizon] = entry

    if not active_models:
        raise RuntimeError("No active models found in registry")

    return active_models


if __name__ == "__main__":
    models = load_active_models()

    print("Active models loaded:\n")
    for h, meta in models.items():
        print(f"+{h}h → {meta['model_name']} (RMSE={meta['rmse']}, R²={meta['r2']})")