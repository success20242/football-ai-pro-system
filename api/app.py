from fastapi import FastAPI
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions

app = FastAPI()

# ✅ Define strict input schema
class MatchInput(BaseModel):
    home_form: float
    away_form: float
    market_edge: float


# 🔮 Single match prediction
@app.post("/predict")
def predict_endpoint(data: MatchInput):

    features = [
        data.home_form,
        data.away_form,
        data.market_edge
    ]

    return predict(features)


# ⚽ LIVE MATCH PREDICTIONS
@app.get("/live")
async def live_predictions():
    return await run_live_predictions()
