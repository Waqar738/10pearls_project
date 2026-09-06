def add_lag_features(df):

    lags = [1, 6, 12, 24, 48, 72, 168]  # 168 = 7 days

    for lag in lags:
        df[f"pm2_5_lag_{lag}"] = df["pm2_5"].shift(lag)

    return df
