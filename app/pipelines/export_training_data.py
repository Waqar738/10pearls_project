import pandas as pd
from app.pipelines.training_dataset import build_training_dataset

if __name__ == "__main__":
    df = build_training_dataset()
    df.to_csv("eda_training_dataset.csv", index=False)
    print("✅ Dataset exported for EDA")