import os
import joblib
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictor")

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")

try:
    model = joblib.load(MODEL_PATH)

    # SAFE CLASS MAPPING
    CLASS_MAP = list(getattr(model, "classes_", ["home", "draw", "away"]))

    logger.info(f"✅ Model loaded: {MODEL_PATH}")
    logger.info(f"📊 Class order: {CLASS_MAP}")

except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None
    CLASS_MAP = ["home", "draw", "away"]


# =========================
# AUTO FEATURE HANDLING
# =========================
def normalize_features(features):
    if not isinstance(features, (list, tuple, np.ndarray)):
        features = []

    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except:
            cleaned.append(0.0)

    return np.array(cleaned, dtype=float).reshape(1, -1)


# =========================
# CORE PREDICTION (FIXED)
# =========================
def predict(features):
    try:
        if model is None:
            raise ValueError("Model not loaded")

        X = normalize_features(features)

        if not np.isfinite(X).all():
            raise ValueError("Invalid features")

        # -------------------------
        # PREDICT PROBABILITIES
        # -------------------------
        probs = model.predict_proba(X)[0]

        # SAFETY CHECK
        if len(probs) != len(CLASS_MAP):
            raise ValueError("Model class mismatch")

        # -------------------------
        # MAP DYNAMICALLY (IMPORTANT FIX)
        # -------------------------
        values = {
            CLASS_MAP[i]: float(probs[i])
            for i in range(len(CLASS_MAP))
        }

        # -------------------------
        # BEST LABEL
        # -------------------------
        label = max(values, key=values.get)
        confidence = values[label]

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "probs": values
        }

    except Exception as e:
        logger.warning(f"⚠️ Prediction error: {e}")

        return {
            "label": "draw",
            "confidence": 0.33,
            "probs": {
                "home": 0.33,
                "draw": 0.34,
                "away": 0.33
            }
        }
