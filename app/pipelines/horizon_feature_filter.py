# pipelines/horizon_feature_filter.py

import pandas as pd


def filter_features_for_horizon(X: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """
    Horizon-aware feature selection.
    MUST always return a DataFrame.
    """

    if X is None:
        raise ValueError("Input features X is None")

    X = X.copy()

    # ✅ TEMPORARY SAFE MODE
    # Do NOT drop any columns until all horizons are stable
    return X