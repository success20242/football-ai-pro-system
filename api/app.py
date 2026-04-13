from fastapi import FastAPI
from models.predict import predict

app = FastAPI()

@app.post("/predict")
def predict_endpoint(features: dict):
    return predict(features["values"])
