def add_rolling_features(df):

    windows = [6, 12, 24, 48]

    for window in windows:
        df[f"pm2_5_roll_mean_{window}"] = (
            df["pm2_5"].rolling(window=window).mean()
        )
        df[f"pm2_5_roll_std_{window}"] = (
            df["pm2_5"].rolling(window=window).std()
        )

    return df
