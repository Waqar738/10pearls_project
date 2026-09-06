import pandas as pd
from fetch_karachi_aqi import fetch_karachi_air_quality
from app.pipelines.fetch_karachi_aqi import fetch_karachi_air_quality


def run_quality_checks(df: pd.DataFrame):
    print("\n=== BASIC INFO ===")
    print(df.info())

    print("\n=== MISSING VALUES ===")
    print(df.isna().sum())

    print("\n=== DESCRIPTIVE STATS ===")
    print(df.describe())

    print("\n=== NEGATIVE VALUE CHECK ===")
    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        negatives = (df[col] < 0).sum()
        print(f"{col}: {negatives} negative values")

    print("\n=== TIMESTAMP CONTINUITY CHECK ===")
    time_diff = df["timestamp"].diff().value_counts()
    print(time_diff)


if __name__ == "__main__":
    df = fetch_karachi_air_quality()
    run_quality_checks(df)