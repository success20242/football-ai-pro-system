import os
import joblib
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictor")

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")

try:
    model = joblib.load(MODEL_PATH)
    CLASS_MAP = list(getattr(model, "classes_", ["home", "draw", "away"]))
    logger.info(f"✅ Model loaded: {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None
    CLASS_MAP = ["home", "draw", "away"]

EXPECTED_FEATURES = 3


# =========================
# FEATURE NORMALIZER
# =========================
def normalize_features(features):
    if not isinstance(features, (list, tuple, np.ndarray)):
        features = [0.0] * EXPECTED_FEATURES

    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except:
            cleaned.append(0.0)

    cleaned = cleaned[:EXPECTED_FEATURES]
    while len(cleaned) < EXPECTED_FEATURES:
        cleaned.append(0.0)

    return np.array(cleaned, dtype=float).reshape(1, -1)


# =========================
# CORE PREDICTION
# =========================
def predict(features):
    try:
        if model is None:
            raise ValueError("Model not loaded")

        X = normalize_features(features)

        if not np.isfinite(X).all():
            raise ValueError("Invalid features")

        probs = model.predict_proba(X)[0]

        # -------------------------
        # MAP CLASS INDEXES
        # -------------------------
        home_p = float(probs[0]) if len(probs) > 0 else 0.33
        draw_p = float(probs[1]) if len(probs) > 1 else 0.33
        away_p = float(probs[2]) if len(probs) > 2 else 0.33

        # -------------------------
        # BEST LABEL
        # -------------------------
        values = {
            "home": home_p,
            "draw": draw_p,
            "away": away_p
        }

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
