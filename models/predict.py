import joblib
import numpy as np

model = joblib.load("models/model.pkl")

# 🔥 FIX: get correct class order from trained model
CLASS_MAP = model.classes_  # e.g. [0,1,2]


def predict(features):

    features = np.array(features).reshape(1, -1)
    probs = model.predict_proba(features)[0]

    result = {
        "home_win": 0.0,
        "draw": 0.0,
        "away_win": 0.0
    }

    for i, cls in enumerate(CLASS_MAP):

        if cls == 0:
            result["home_win"] = float(probs[i])
        elif cls == 1:
            result["draw"] = float(probs[i])
        elif cls == 2:
            result["away_win"] = float(probs[i])

    return result
