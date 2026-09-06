import requests
import pandas as pd
from datetime import datetime
from app.db.mongo import get_db


def download_openmeteo_historical():

    latitude = 24.8607
    longitude = 67.0011

    start_date = "2024-09-01"
    end_date = "2025-02-01"

    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&start_date={start_date}"
        f"&end_date={end_date}"
        "&hourly="
        "pm2_5,"
        "pm10,"
        "temperature_2m,"
        "relativehumidity_2m,"
        "windspeed_10m"
        "&timezone=Asia/Karachi"
    )

    print("Fetching 5 months historical data from Open-Meteo...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data["hourly"])

    df["datetime"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["time"])

    print("Rows downloaded:", len(df))

    db = get_db()
    collection = db["historical_hourly_data"]

    collection.delete_many({})
    collection.insert_many(df.to_dict("records"))

    print("✅ Historical data saved to Mongo")


if __name__ == "__main__":
    download_openmeteo_historical()
