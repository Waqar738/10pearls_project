import numpy as np
import pandas as pd


def add_time_features(df):

    if "datetime" not in df.columns:
        return df  # skip if missing

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    df["hour"] = df["datetime"].dt.hour
    df["day"] = df["datetime"].dt.day
    df["month"] = df["datetime"].dt.month
    df["dayofweek"] = df["datetime"].dt.dayofweek

    return df
