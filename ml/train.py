import argparse
import json
import pickle
import random
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from feature_extraction import FEATURE_NAMES, vectorize

SEED = 42
ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "backend" / "model"


def load_data(path: Path) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.read_csv(path).dropna(subset=["url", "label"]).drop_duplicates(subset=["url"])
    frame["label"] = frame["label"].astype(str).str.lower().map({"0": 0, "1": 1, "legitimate": 0, "phishing": 1})
    frame = frame.dropna(subset=["label"])
    frame = frame[frame["url"].map(lambda value: isinstance(value, str) and value.startswith(("http://", "https://")))]
    if frame["label"].nunique() != 2 or len(frame) < 10:
        raise ValueError("Dataset must contain both labels and at least 10 valid rows")
    x = np.vstack([vectorize(url)[0] for url in frame["url"]])
    return x, frame["label"].astype("int32").to_numpy()


def build_model(input_size: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_size,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(), loss="binary_crossentropy", metrics=["accuracy", tf.keras.metrics.Precision(name="precision"), tf.keras.metrics.Recall(name="recall"), tf.keras.metrics.AUC(name="roc_auc")])
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "ml" / "data" / "raw" / "urls.csv")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)
    x, y = load_data(args.input)
    x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.3, stratify=y, random_state=SEED)
    x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=SEED)
    scaler = StandardScaler().fit(x_train)
    x_train, x_val, x_test = scaler.transform(x_train), scaler.transform(x_val), scaler.transform(x_test)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model = build_model(len(FEATURE_NAMES))
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True), tf.keras.callbacks.ModelCheckpoint(MODEL_DIR / "phishing_model.keras", monitor="val_loss", save_best_only=True), tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", patience=4, factor=0.5)]
    history = model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=args.epochs, batch_size=args.batch_size, callbacks=callbacks, verbose=1)
    with (MODEL_DIR / "scaler.pkl").open("wb") as file:
        pickle.dump(scaler, file)
    (MODEL_DIR / "feature_config.json").write_text(json.dumps({"feature_names": FEATURE_NAMES, "seed": SEED}, indent=2), encoding="utf-8")
    probabilities = model.predict(x_test, verbose=0).ravel()
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {"accuracy": accuracy_score(y_test, predictions), "precision": precision_score(y_test, predictions, zero_division=0), "recall": recall_score(y_test, predictions, zero_division=0), "f1": f1_score(y_test, predictions, zero_division=0), "roc_auc": roc_auc_score(y_test, probabilities)}
    (MODEL_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Saved model and preprocessing artifacts to {MODEL_DIR}")


if __name__ == "__main__":
    main()
