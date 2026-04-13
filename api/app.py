from fastapi import FastAPI
from pydantic import BaseModel
from models.predict import predict

app = FastAPI()

# ✅ Define strict input schema
class MatchInput(BaseModel):
    home_form: float
    away_form: float
    market_edge: float

@app.post("/predict")
def predict_endpoint(data: MatchInput):

    features = [
        data.home_form,
        data.away_form,
        data.market_edge
    ]

    return predict(features)
