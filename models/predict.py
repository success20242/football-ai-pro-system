import joblib
import numpy as np

model = joblib.load("models/model.pkl")

# Expected: model.classes_ = [0, 1, 2]
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
        # =========================
        # VALIDATION
        # =========================
        if features is None:
            raise ValueError("Features are None")

        features = np.asarray(features, dtype=float).reshape(1, -1)

        if not np.isfinite(features).all():
            raise ValueError("Invalid feature values (NaN or Inf detected)")

        # =========================
        # PREDICT
        # =========================
        probs = model.predict_proba(features)[0]

        # =========================
        # SAFE DEFAULT OUTPUT
        # =========================
        result = {
            "home_win": 0.0,
            "draw": 0.0,
            "away_win": 0.0
        }

        # =========================
        # DIRECT CLASS MAPPING (CORRECT WAY)
        # =========================
        for i, cls in enumerate(CLASS_MAP):
            prob = float(probs[i])

            if cls == 0 or str(cls).lower() in ["home"]:
                result["home_win"] = prob

            elif cls == 1 or str(cls).lower() in ["draw", "x"]:
                result["draw"] = prob

            elif cls == 2 or str(cls).lower() in ["away"]:
                result["away_win"] = prob

        # =========================
        # FINAL SAFETY CHECK
        # =========================
        total = sum(result.values())

        if total > 0:
            result = {k: v / total for k, v in result.items()}

        return result

    except Exception as e:
        print(f"⚠️ Prediction error: {e}")

        # stable fallback (never breaks API)
        return {
            "home_win": 0.33,
            "draw": 0.34,
            "away_win": 0.33
        }
