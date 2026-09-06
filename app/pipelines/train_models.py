import joblib
import io
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from gridfs import GridFS

from app.db.mongo import get_db, get_model_registry


def evaluate_model(model, X_val, y_val):
    preds = model.predict(X_val)

    rmse = mean_squared_error(y_val, preds, squared=False)
    mae = mean_absolute_error(y_val, preds)
    r2 = r2_score(y_val, preds)

    return rmse, mae, r2


def save_model_to_gridfs(model, model_name, horizon):
    db = get_db()
    fs = GridFS(db)

    model_bytes = io.BytesIO()
    joblib.dump(model, model_bytes)
    model_bytes.seek(0)

    gridfs_id = fs.put(
        model_bytes.read(),
        filename=f"{model_name}_h{horizon}",
        uploadDate=datetime.utcnow()
    )

    return gridfs_id


def register_model(model_name, horizon, rmse, mae, r2, gridfs_id, features, run_id):
    registry = get_model_registry()

    model_doc = {
        "model_name": model_name,
        "horizon": horizon,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "gridfs_id": gridfs_id,
        "features": features,
        "run_id": run_id,
        "status": "candidate",
        "is_best": False,
        "registered_at": datetime.utcnow()
    }

    registry.insert_one(model_doc)


def train_all_models(X_train, y_train, X_val, y_val, horizon, run_id):

    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from xgboost import XGBRegressor

    registry = get_model_registry()

    models = {
        "random_forest": RandomForestRegressor(n_estimators=200, random_state=42),
        "gradient_boosting": GradientBoostingRegressor(),
        "ridge": Ridge(),
        "xgboost": XGBRegressor(objective="reg:squarederror")
    }

    results = []

    for name, model in models.items():
        print(f"\n🔹 Training {name} (H{horizon})")

        model.fit(X_train, y_train)

        rmse, mae, r2 = evaluate_model(model, X_val, y_val)

        print(f"RMSE={rmse:.4f} | MAE={mae:.4f} | R2={r2:.4f}")

        gridfs_id = save_model_to_gridfs(model, name, horizon)

        model_doc = {
            "model_name": name,
            "horizon": horizon,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "gridfs_id": gridfs_id,
            "features": list(X_train.columns),
            "run_id": run_id,
            "status": "candidate",
            "is_best": False,
            "registered_at": datetime.utcnow()
        }

        registry.insert_one(model_doc)

        results.append(model_doc)

    # -------------------------------------------------
    # Select Best Model (Lowest RMSE)
    # -------------------------------------------------

    best_model = min(results, key=lambda x: x["rmse"])

    print(f"\n🏆 Best model for H{horizon}: {best_model['model_name']}")

    # Archive previous production model
    registry.update_many(
        {"horizon": horizon, "status": "production"},
        {"$set": {"status": "archived", "is_best": False}}
    )

    # Promote best model
    registry.update_one(
        {
            "horizon": horizon,
            "run_id": run_id,
            "model_name": best_model["model_name"]
        },
        {
            "$set": {
                "status": "production",
                "is_best": True
            }
        }
    )

    print("✅ Production model updated")