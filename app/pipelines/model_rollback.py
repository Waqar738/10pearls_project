from app.db.mongo import get_model_registry


def rollback_model(horizon: int, run_id: str):

    registry = get_model_registry()

    target_model = registry.find_one({
        "horizon": horizon,
        "run_id": run_id
    })

    if not target_model:
        raise RuntimeError("Model version not found")

    registry.update_many(
        {"horizon": horizon},
        {"$set": {"is_best": False}}
    )

    registry.update_one(
        {"_id": target_model["_id"]},
        {"$set": {"is_best": True}}
    )

    print("✅ Rollback successful")
