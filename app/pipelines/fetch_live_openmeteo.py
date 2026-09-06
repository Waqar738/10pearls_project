import requests
import pandas as pd


def fetch_live_weather():

    latitude = 24.8607
    longitude = 67.0011

    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        "&hourly="
        "pm2_5,"
        "pm10,"
        "temperature_2m,"
        "relativehumidity_2m,"
        "windspeed_10m"
        "&forecast_days=3"
        "&timezone=Asia/Karachi"
    )

    print("Fetching live 3-day weather forecast...")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["datetime"] = pd.to_datetime(df["time"])
    df = df.drop(columns=["time"])

    print("Live rows fetched:", len(df))

    return df
