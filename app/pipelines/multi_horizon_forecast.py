import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

from prepare_forecast_target import build_forecasting_dataset
from horizon_feature_filter import filter_features_for_horizon


HORIZONS = [1, 6, 24, 48]


def train_for_horizon(horizon: int):
    # -----------------------------------
    # Build forecasting dataset
    # -----------------------------------
    X, y = build_forecasting_dataset(horizon=horizon)

    # -----------------------------------
    # ✅ HORIZON-AWARE FEATURE FILTERING
    # -----------------------------------
    X = filter_features_for_horizon(X, horizon)

    # 🔍 DEBUG (DO NOT REMOVE YET)
    print(f"H{horizon}: features after filtering = {X.shape[1]}")

    # -----------------------------------
    # Time-based split (NO SHUFFLE)
    # -----------------------------------
    split_idx = int(len(X) * 0.8)

    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]

    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]

    # -----------------------------------
    # Model (Baseline Ridge)
    # -----------------------------------
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    # -----------------------------------
    # Evaluation
    # -----------------------------------
    y_pred = model.predict(X_test)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    return rmse, r2


if __name__ == "__main__":
    print("\nMulti-Horizon Forecasting Results (Horizon-Aware)\n")

    for h in HORIZONS:
        rmse, r2 = train_for_horizon(h)
        print(f"Horizon +{h}h → RMSE: {rmse:.2f}, R²: {r2:.3f}")