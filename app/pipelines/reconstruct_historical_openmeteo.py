import requests
import pandas as pd
from datetime import datetime, timedelta
from app.db.mongo import get_db


def reconstruct_historical_openmeteo(days: int = 150):

    latitude = 24.8607
    longitude = 67.0011

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    all_data = []

    print(f"Reconstructing {days} days of historical data...")

    current_start = start_date

    while current_start < end_date:

        current_end = min(current_start + timedelta(days=10), end_date)

        url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            f"&start_date={current_start}"
            f"&end_date={current_end}"
            "&hourly=pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,"
            "sulphur_dioxide,ozone"
            "&timezone=Asia/Karachi"
        )

        print(f"Fetching {current_start} → {current_end}")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()

        if "hourly" not in data:
            print("⚠️ No hourly data returned")
            current_start = current_end + timedelta(days=1)
            continue

        df_chunk = pd.DataFrame(data["hourly"])
        df_chunk["datetime"] = pd.to_datetime(df_chunk["time"])
        df_chunk = df_chunk.drop(columns=["time"])

        all_data.append(df_chunk)

        current_start = current_end + timedelta(days=1)

    if not all_data:
        raise RuntimeError("No historical data reconstructed.")

    df_final = pd.concat(all_data).reset_index(drop=True)

    print("Total reconstructed rows:", len(df_final))

    # Save to Mongo
    db = get_db()
    collection = db["historical_hourly_data"]

    collection.delete_many({})
    collection.insert_many(df_final.to_dict("records"))

    print("✅ Historical reconstruction complete and saved to Mongo")


if __name__ == "__main__":
    reconstruct_historical_openmeteo(days=150)

