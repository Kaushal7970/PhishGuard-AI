import json
from pathlib import Path
import pickle

from fastapi import HTTPException

from app.config import settings
from app.services.feature_extractor import indicators, vectorize


class Predictor:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None

    def _load(self) -> None:
        if self.model is not None and self.scaler is not None:
            return
        model_path = self.model_dir / "phishing_model.keras"
        scaler_path = self.model_dir / "scaler.pkl"
        if not model_path.exists() or not scaler_path.exists():
            raise HTTPException(status_code=503, detail="Trained model is unavailable. Run ml/train.py first.")
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(model_path)
            with scaler_path.open("rb") as file:
                self.scaler = pickle.load(file)
        except Exception as exc:
            self.model = None
            self.scaler = None
            raise HTTPException(status_code=503, detail="Trained model could not be loaded") from exc

    def predict(self, url: str) -> dict:
        self._load()
        probability = float(self.model.predict(self.scaler.transform(vectorize(url)), verbose=0)[0][0])
        risk_score = round(probability * 100, 2)
        if risk_score < 30:
            risk_level, prediction = "LOW", "LEGITIMATE"
        elif risk_score < 70:
            risk_level, prediction = "MEDIUM", "SUSPICIOUS"
        else:
            risk_level, prediction = "HIGH", "PHISHING"
        return {"url": url, "prediction": prediction, "probability": round(probability, 6), "risk_score": risk_score, "risk_level": risk_level, "indicators": indicators(url)}


predictor = Predictor(settings.model_dir)
