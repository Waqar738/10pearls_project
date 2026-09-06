"""
Feature Pipeline Runner
-----------------------
- Builds latest feature dataframe
- Writes features to MongoDB feature store
- Optimized bulk insert for CI/CD
"""

import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app.pipelines.final_feature_table import build_final_dataframe
from app.db.mongo import get_feature_store


def run():
    print("🚀 Starting feature pipeline")

    df = build_final_dataframe()

    if df is None or df.empty:
        raise RuntimeError("❌ Feature pipeline produced empty dataframe")

    collection = get_feature_store()

    # 🔥 CLEAR OLD DATA (prevent duplication)
    print("🧹 Clearing old feature store data...")
    collection.delete_many({})

    # 🔥 BULK INSERT (FAST)
    records = df.to_dict("records")

    if records:
        collection.insert_many(records)
        print(f"✅ Inserted {len(records)} records successfully")
    else:
        print("⚠ No records to insert")

    print("🎯 Feature pipeline completed successfully")


if __name__ == "__main__":
    run()
