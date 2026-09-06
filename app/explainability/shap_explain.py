import joblib
import shap
import pandas as pd
import matplotlib.pyplot as plt

from app.pipelines.final_feature_table import build_training_dataset


def explain_model():

    # 1️⃣ Load training dataset
    df = build_training_dataset()

    # Load 1-day target
    target_col = "target_h1"

    # Load model
    model = joblib.load("models/rf_model_h1.joblib")

    # Get feature columns exactly used in training
    feature_cols = model.feature_names_in_

    X = df[feature_cols]

    # 2️⃣ Create SHAP explainer
    explainer = shap.TreeExplainer(model)

    # Use small sample for speed
    X_sample = X.sample(200, random_state=42)

    shap_values = explainer.shap_values(X_sample)

    # 3️⃣ Summary plot
    shap.summary_plot(shap_values, X_sample)

    # 4️⃣ Bar importance plot
    shap.summary_plot(shap_values, X_sample, plot_type="bar")

    plt.show()


if __name__ == "__main__":
    explain_model()
