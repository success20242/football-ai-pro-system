import joblib
import numpy as np

model = joblib.load("models/model.pkl")

def predict(features):

    features = np.array(features).reshape(1, -1)
    probs = model.predict_proba(features)[0]

    return {
        "away_win": float(probs[0]),
        "draw": float(probs[1]),
        "home_win": float(probs[2])
    }
