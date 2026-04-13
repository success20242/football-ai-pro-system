import joblib
import numpy as np

model = joblib.load("models/model.pkl")

def predict(features):

    features = np.array(features).reshape(1, -1)

    probs = model.predict_proba(features)[0]

    # safer generic mapping
    return {
        "class_0": float(probs[0]),
        "class_1": float(probs[1]),
        "class_2": float(probs[2]),
    }
