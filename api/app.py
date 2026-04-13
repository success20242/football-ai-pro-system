from fastapi import FastAPI
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.betting_engine import run_betting_engine  # 🔥 NEW (betting engine)

app = FastAPI()


# =========================
# REQUEST SCHEMA
# =========================
class MatchInput(BaseModel):
    home_form: float
    away_form: float
    market_edge: float


# =========================
# SINGLE MATCH PREDICTION
# =========================
@app.post("/predict")
def predict_endpoint(data: MatchInput):

    features = [
        data.home_form,
        data.away_form,
        data.market_edge
    ]

    return predict(features)


# =========================
# LIVE MATCH PREDICTIONS
# =========================
@app.get("/live")
async def live_predictions():
    return await run_live_predictions()


# =========================
# 💰 BETTING ENGINE (NEW)
# =========================
@app.get("/bets")
async def bets():
    return await run_betting_engine()
