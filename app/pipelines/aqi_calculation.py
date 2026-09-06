import pandas as pd
from app.pipelines.fetch_karachi_aqi import fetch_karachi_air_quality


def calculate_aqi_pm25(pm25: float) -> int:
    """
    EPA AQI calculation for PM2.5
    """
    breakpoints = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]

    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm25 <= c_high:
            return round(
                ((i_high - i_low) / (c_high - c_low))
                * (pm25 - c_low)
                + i_low
            )

    return None


def add_aqi_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["aqi_pm25"] = df["pm2_5"].apply(calculate_aqi_pm25)
    return df


if __name__ == "__main__":
    df = fetch_karachi_air_quality()
    df = add_aqi_column(df)

    print(df[["pm2_5", "aqi_pm25", "timestamp"]].head())
    print("\nAQI stats:")
    print(df["aqi_pm25"].describe())