import argparse
import json
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from feature_extraction import vectorize
from train import SEED, load_data

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "backend" / "model"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=ROOT / "ml" / "data" / "raw" / "urls.csv")
    args = parser.parse_args()
    model_path = MODEL_DIR / "phishing_model.keras"
    scaler_path = MODEL_DIR / "scaler.pkl"
    if not model_path.exists() or not scaler_path.exists():
        raise FileNotFoundError("Saved model artifacts are missing. Run ml/train.py first.")
    import tensorflow as tf
    x, y = load_data(args.data)
    _, x_test, _, y_test = train_test_split(x, y, test_size=0.3, stratify=y, random_state=SEED)
    _, x_test, _, y_test = train_test_split(x_test, y_test, test_size=0.5, stratify=y_test, random_state=SEED)
    with scaler_path.open("rb") as file:
        scaler = pickle.load(file)
    model = tf.keras.models.load_model(model_path)
    probabilities = model.predict(scaler.transform(x_test), verbose=0).ravel()
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities),
    }
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    cm = confusion_matrix(y_test, predictions)
    ConfusionMatrixDisplay(cm, display_labels=["Legitimate", "Phishing"]).plot(cmap="Blues")
    plt.tight_layout()
    plt.savefig(MODEL_DIR / "confusion_matrix.png")
    plt.close()
    false_positive, true_positive, _ = roc_curve(y_test, probabilities)
    plt.plot(false_positive, true_positive, label=f"ROC-AUC = {metrics['roc_auc']:.3f}")
    plt.plot([0, 1], [0, 1], "--", color="gray")
    plt.xlabel("False positive rate")
    plt.ylabel("True positive rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig(MODEL_DIR / "roc_curve.png")
    plt.close()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
