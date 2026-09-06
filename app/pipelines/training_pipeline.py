import io
import joblib
from datetime import datetime

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from gridfs import GridFS

from app.pipelines.training_dataset import build_training_dataset
from app.db.mongo import get_model_registry, get_database


# ---------------------------------------------------
# TRAIN SINGLE HORIZON
# ---------------------------------------------------
def train_horizon(df: pd.DataFrame, horizon: int):

    print(f"🔥 Starting training for horizon {horizon}")

    target_col = f"target_h{horizon}"

    if target_col not in df.columns:
        raise ValueError(f"{target_col} not found in dataset")

    X = df.drop(columns=["datetime", "target_h1", "target_h2", "target_h3"])
    y = df[target_col]

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    preds = model.predict(X)

    # Fixed: Calculate RMSE manually
    rmse = mean_squared_error(y, preds) ** 0.5
    mae = mean_absolute_error(y, preds)
    r2 = r2_score(y, preds)

    print("✅ Model trained")
    print("RMSE:", rmse)
    print("MAE:", mae)
    print("R2:", r2)

    # ---------------------------------------------------
    # STORE MODEL IN GRIDFS
    # ---------------------------------------------------
    db = get_database()
    fs = GridFS(db)
    registry = get_model_registry()

    # Serialize model
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)

    # Remove old model for this horizon
    old_models = registry.find({"horizon": horizon})
    for doc in old_models:
        if "gridfs_id" in doc:
            fs.delete(doc["gridfs_id"])

    # Save new model
    file_id = fs.put(
        buffer.read(),
        filename=f"rf_h{horizon}.pkl"
    )

    print("💾 Model stored in GridFS")

    # Remove old best flag
    registry.update_many(
        {"horizon": horizon},
        {"$set": {"is_best": False}}
    )

    registry.insert_one({
        "model_name": f"rf_h{horizon}",
        "horizon": horizon,
        "gridfs_id": file_id,
        "features": list(X.columns),
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2),
        "created_at": datetime.utcnow(),
        "is_best": True,
        "status": "production"
    })

    print("📦 Model metadata stored in Mongo")

    return {
        "horizon": horizon,
        "rmse": float(rmse),
        "mae": float(mae),
        "r2": float(r2)
    }


# ---------------------------------------------------
# RUN TRAINING PIPELINE
# ---------------------------------------------------
def run_training(horizon: int):

    if horizon not in [1, 2, 3]:
        raise ValueError("Horizon must be 1, 2, or 3")

    print("🚀 Building training dataset")

    df = build_training_dataset()

    print("Dataset shape:", df.shape)

    result = train_horizon(df, horizon)

    print("🎯 Training completed successfully")

    return result


# ---------------------------------------------------
# RUN ALL HORIZONS
# ---------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting training pipeline...")
    
    for h in [1, 2, 3]:
        print(f"\n{'='*50}")
        print(f"Training Horizon {h}")
        print('='*50)
        try:
            result = run_training(h)
            print(f"✅ Horizon {h} complete: RMSE={result['rmse']:.2f}, R²={result['r2']:.3f}")
        except Exception as e:
            print(f"❌ Horizon {h} failed: {e}")
    
    print("\n🎯 Training pipeline complete!")