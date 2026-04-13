from fastapi import FastAPI
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.betting_engine import run_betting_engine
from engine.institutional_engine import run_institutional_engine  # 🔥 NEW

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
# 💰 BETTING ENGINE
# =========================
@app.get("/bets")
async def bets():
    return await run_betting_engine()


# =========================
# 🏦 INSTITUTIONAL ENGINE (NEW)
# =========================
@app.get("/institutional")
async def institutional():
    return await run_institutional_engine()
