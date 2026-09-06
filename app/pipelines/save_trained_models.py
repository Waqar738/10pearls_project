from app.pipelines.train_baseline_model import train_and_return_model

if __name__ == "__main__":
    for horizon in [1, 3, 7]:
        train_and_return_model(horizon)

    print("✅ All models trained and saved")
