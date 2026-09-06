import requests
import pandas as pd
from datetime import datetime, timedelta
from app.db.mongo import get_database

def download_historical_data():
    """
    Downloads historical hourly air quality data from AQICN API
    and stores it in MongoDB.
    """

    # Karachi coordinates
    latitude = 24.8608
    longitude = 67.0104
    
    # AQICN API token - get from https://aqicn.org/api/
    token = "593d56f2c0edba0cb9ccd27eac295534c4206b65"
    
    print("🌍 Fetching AQI data from AQICN for Karachi...")
    print(f"📍 Coordinates: {latitude}, {longitude}")
    
    url = f"https://api.waqi.info/feed/geo:{latitude};{longitude}/?token={token}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "ok":
            print("❌ API Error:", data.get("data", "Unknown error"))
            print("⚠️ Using sample data instead...")
            use_sample_data()
            return
        
        aqi_data = data["data"]
        aqi_value = aqi_data.get("aqi", "N/A")
        
        print(f"✅ Current AQI for Karachi: {aqi_value}")
        print("📊 Note: Historical data requires AQICN Pro subscription.")
        print("💡 Using sample dataset for training...")
        
        # Use the sample dataset that came with the repo
        use_sample_data()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ Using sample data for training...")
        use_sample_data()

def use_sample_data():
    """
    Loads the sample dataset that came with the repository
    """
    try:
        df = pd.read_csv("eda_training_dataset.csv")
        
        # Convert to format expected by the pipeline
        df["datetime"] = pd.to_datetime(df["datetime"])
        
        # Store in Mongo
        db = get_database()
        collection = db["historical_hourly_data"]
        
        # Clear old data
        collection.delete_many({})
        
        records = df.to_dict("records")
        collection.insert_many(records)
        
        print(f"✅ Inserted {len(records)} sample records into MongoDB")
        print(f"📅 Data range: {df['datetime'].min()} to {df['datetime'].max()}")
        
    except Exception as e:
        print(f"❌ Failed to load sample data: {e}")

if __name__ == "__main__":
    download_historical_data()