import joblib
import numpy as np

model = joblib.load("models/model.pkl")

# =========================
# SAFE CLASS HANDLING
# =========================
CLASS_MAP = list(model.classes_)


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
        # -------------------------
        # VALIDATE INPUT
        # -------------------------
        if features is None:
            raise ValueError("Features are None")

        features = np.array(features, dtype=float).reshape(1, -1)

        if np.isnan(features).any():
            raise ValueError("NaN detected in features")

        # -------------------------
        # MODEL PREDICTION
        # -------------------------
        probs = model.predict_proba(features)[0]

        # -------------------------
        # INITIAL OUTPUT
        # -------------------------
        result = {
            "home_win": 0.0,
            "draw": 0.0,
            "away_win": 0.0
        }

        # -------------------------
        # MAP CLASSES SAFELY
        # -------------------------
        for i, cls in enumerate(CLASS_MAP):

            prob = float(probs[i])

            if cls in [0, "HOME", "home", 1]:
                result["home_win"] = prob

            elif cls in [1, "DRAW", "draw", "X"]:
                result["draw"] = prob

            elif cls in [2, "AWAY", "away", "2"]:
                result["away_win"] = prob

        # -------------------------
        # FINAL SAFETY CHECK (NORMALIZE)
        # -------------------------
        total = sum(result.values())

        if total > 0:
            result = {k: v / total for k, v in result.items()}

        return result

    except Exception as e:
        print(f"⚠️ Prediction error: {e}")

        # fallback (NEVER BREAK API)
        return {
            "home_win": 0.33,
            "draw": 0.34,
            "away_win": 0.33
        }
