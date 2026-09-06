import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from app.db.mongo import get_db


def run_eda():

    db = get_db()
    data = list(db["historical_hourly_data"].find({}, {"_id": 0}))
    df = pd.DataFrame(data)

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime")

    print("Shape:", df.shape)
    print("\nSummary Statistics:\n", df.describe())

    # 📈 AQI Trend
    plt.figure()
    plt.plot(df["datetime"], df["pm2_5"])
    plt.title("PM2.5 Trend Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # 📊 Histogram
    plt.figure()
    plt.hist(df["pm2_5"], bins=30)
    plt.title("Distribution of PM2.5")
    plt.show()

    # 🔥 Correlation Heatmap
    plt.figure()
    sns.heatmap(df.drop(columns=["datetime"]).corr(), annot=True)
    plt.title("Correlation Heatmap")
    plt.show()


if __name__ == "__main__":
    run_eda()
