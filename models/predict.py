import joblib
import numpy as np

model = joblib.load("models/model.pkl")

def predict(features):
    probs = model.predict_proba([features])[0]

    return {
        "home": probs[2],
        "draw": probs[1],
        "away": probs[0]
    }
