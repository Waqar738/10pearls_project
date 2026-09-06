from app.db.mongo import get_model_registry


def select_best_model(horizon):

    registry = get_model_registry()

    # Get candidate models for this horizon
    candidates = list(
        registry.find(
            {"horizon": horizon, "status": "candidate"}
        ).sort("rmse", 1)
    )

    if not candidates:
        raise RuntimeError("No candidate models found")

    best_model = candidates[0]

    # Reset previous production models
    registry.update_many(
        {"horizon": horizon},
        {"$set": {"is_best": False, "status": "archived"}}
    )

    # Promote best model
    registry.update_one(
        {"_id": best_model["_id"]},
        {"$set": {"is_best": True, "status": "production"}}
    )

    return best_model
