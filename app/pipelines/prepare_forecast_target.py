import pandas as pd
from app.pipelines.final_feature_table import build_final_dataframe


def build_forecasting_dataset(horizon: int = 1):
    """
    horizon = number of hours ahead to predict
    """

    X, y = build_final_dataset()

    # Shift target INTO THE FUTURE
    y_future = y.shift(-horizon)

    # Align X and y
    X = X.iloc[:-horizon].reset_index(drop=True)
    y_future = y_future.iloc[:-horizon].reset_index(drop=True)

    return X, y_future


if __name__ == "__main__":
    X, y = build_forecasting_dataset(horizon=1)

    print("Forecasting dataset shape:")
    print("X:", X.shape)
    print("y:", y.shape)

    print("\nFirst 5 target values (future AQI):")
    print(y.head())