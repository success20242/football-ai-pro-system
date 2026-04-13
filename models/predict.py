import joblib
import numpy as np

model = joblib.load("models/model.pkl")

def predict(features):

    features = np.array(features).reshape(1, -1)
    probs = model.predict_proba(features)[0]

    return {
        "loss": float(probs[0]),
        "win": float(probs[1])
    }
