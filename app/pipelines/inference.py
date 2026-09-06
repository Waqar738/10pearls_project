import argparse
import io
from datetime import datetime

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from gridfs import GridFS

from app.pipelines.training_dataset import build_training_dataset
from app.db.mongo import (
    get_model_registry,
    get_database,
    get_feature_store
)


# -------------------------------------------
# Train One Horizon
# -------------------------------------------
def train_horizon(df, horizon: int):

    target_column = f"target_h{horizon}"

    if target_column not in df.columns:
        raise RuntimeError(f"Missing target column: {target_column}")

    feature_cols = [
        "hour",
        "day",
        "month",
        "lag_1",
        "lag_3",
        "lag_6",
        "roll_mean_6",
        "roll_mean_12",
    ]

    X = df[feature_cols]
    y = df[target_column]

    split_index = int(len(df) * 0.8)

    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    rmse = mean_squared_error(y_test, preds, squared=False)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"✅ Horizon {horizon} trained")
    print("RMSE:", rmse)
    print("MAE:", mae)
    print("R2:", r2)

    # -------------------------------------------
    # Save Model to GridFS
    # -------------------------------------------
    db = get_database()
    fs = GridFS(db)

    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    buffer.seek(0)

    file_id = fs.put(
        buffer.read(),
        filename=f"rf_h{horizon}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    )

    print("📁 Model stored in GridFS")

    # -------------------------------------------
    # Register Model
    # -------------------------------------------
    registry = get_model_registry()

    registry.update_many(
        {"horizon": horizon, "status": "production"},
        {"$set": {"status": "archived", "is_best": False}}
    )

    registry.insert_one({
        "model_name": "random_forest",
        "horizon": horizon,
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "gridfs_id": file_id,
        "features": feature_cols,
        "status": "production",
        "is_best": True,
        "registered_at": datetime.utcnow()
    })

    print("📦 Model registered in MongoDB")


# -------------------------------------------
# Run Training
# -------------------------------------------
def run_training(horizon: int):

    print("🔥 Starting Daily Training Pipeline")

    df = build_training_dataset()

    print("✅ Training dataset built:", df.shape)

    # -------------------------------------------
    # Populate Feature Store
    # -------------------------------------------
    feature_store = get_feature_store()

    feature_columns = [
        col for col in df.columns
        if not col.startswith("target_")
    ]

    feature_docs = df[feature_columns].to_dict(orient="records")

    feature_store.delete_many({})

    if feature_docs:
        feature_store.insert_many(feature_docs)

    print(f"📦 Feature store populated: {len(feature_docs)} documents")

    # -------------------------------------------
    # Train model
    # -------------------------------------------
    train_horizon(df, horizon)


# -------------------------------------------
# CLI Entry
# -------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizon", type=int, required=True)
    args = parser.parse_args()

    run_training(args.horizon)