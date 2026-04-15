import os
import joblib
import numpy as np
import logging

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictor")

# =========================
# LOAD MODEL (SAFE)
# =========================
MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")

try:
    model = joblib.load(MODEL_PATH)
    CLASS_MAP = list(getattr(model, "classes_", [0, 1, 2]))
    logger.info(f"✅ Model loaded: {MODEL_PATH}")
except Exception as e:
    logger.error(f"❌ Failed to load model: {e}")
    model = None
    CLASS_MAP = [0, 1, 2]


# =========================
# CONFIG (CRITICAL)
# =========================
EXPECTED_FEATURES = 3  # 🔥 MUST MATCH your feature pipeline


# =========================
# SAFE FEATURE NORMALIZER
# =========================
def normalize_features(features):
    """
    Ensures model ALWAYS gets correct shape
    """

    if not isinstance(features, (list, tuple, np.ndarray)):
        return np.zeros((1, EXPECTED_FEATURES))

    cleaned = []

    for f in features:
        try:
            cleaned.append(float(f))
        except Exception:
            cleaned.append(0.0)

    # enforce exact shape
    cleaned = cleaned[:EXPECTED_FEATURES]

    while len(cleaned) < EXPECTED_FEATURES:
        cleaned.append(0.0)

    return np.asarray(cleaned, dtype=float).reshape(1, -1)


# =========================
# SAFE CLASS MAPPER
# =========================
def map_probabilities(probs):
    """
    Maps model output → standard format
    """

    result = {
        "home_win": 0.0,
        "draw": 0.0,
        "away_win": 0.0
    }

    try:
        for i, cls in enumerate(CLASS_MAP):
            prob = float(probs[i]) if i < len(probs) else 0.0

            cls_str = str(cls).lower()

            if cls == 0 or "home" in cls_str:
                result["home_win"] = prob

            elif cls == 1 or "draw" in cls_str or cls_str == "x":
                result["draw"] = prob

            elif cls == 2 or "away" in cls_str:
                result["away_win"] = prob

        # normalize (safety)
        total = sum(result.values())

        if total > 0:
            result = {k: v / total for k, v in result.items()}

    except Exception as e:
        logger.warning(f"⚠️ Mapping error: {e}")

    return result


# =========================
# MAIN PREDICT FUNCTION
# =========================
def predict(features):
    """
    Returns:
    {
        "home_win": float,
        "draw": float,
        "away_win": float
    }
    """

    try:
        # =========================
        # MODEL CHECK
        # =========================
        if model is None:
            raise ValueError("Model not loaded")

        # =========================
        # FEATURE NORMALIZATION
        # =========================
        X = normalize_features(features)

        if not np.isfinite(X).all():
            raise ValueError("Invalid feature values (NaN/Inf)")

        # =========================
        # PREDICT
        # =========================
        probs = model.predict_proba(X)[0]

        # =========================
        # MAP OUTPUT
        # =========================
        return map_probabilities(probs)

    except Exception as e:
        logger.warning(f"⚠️ Prediction error: {e}")

        # =========================
        # FALLBACK (NEVER BREAK API)
        # =========================
        return {
            "home_win": 0.33,
            "draw": 0.34,
            "away_win": 0.33
        }
