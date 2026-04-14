from fastapi import FastAPI, Body
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest
from features.real_features import build_real_features
from data.football_api import get_live_matches

app = FastAPI()


# =========================
# INPUT MODEL (RAW MATCH ONLY)
# =========================
class MatchInput(BaseModel):
    match: dict


# =========================
# REAL FEATURE PREDICTION
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    match = data.match

    # 🟢 USE REAL FEATURE ENGINE
    features = await build_real_features(match)

    return predict(features)


# =========================
# LIVE PREDICTIONS (REAL PIPELINE)
# =========================
@app.get("/live")
async def live_predictions():
    return await run_live_predictions()


# =========================
# BACKTEST (REAL FORMAT)
# =========================
@app.post("/backtest")
async def backtest_endpoint(dataset: list = Body(...)):

    """
    Expected:
    [
        {
            "match": {...},
            "label": 0/1/2
        }
    ]
    """

    return run_backtest(dataset)
