import sys
import os

# Add project root to PYTHONPATH FIRST
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from db.mongo import model_registry


def get_best_model(horizon: int):
    return model_registry.find_one(
        {"horizon": horizon, "is_best": True},
        {"_id": 0}
    )


if __name__ == "__main__":
    print(get_best_model(1))
