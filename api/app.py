from fastapi import FastAPI, Body
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest

app = FastAPI()


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
# LIVE PREDICTIONS
# =========================
@app.get("/live")
async def live_predictions():
    return await run_live_predictions()


# =========================
# BACKTEST (FIXED)
# =========================
@app.post("/backtest")
async def backtest_endpoint(dataset: list = Body(...)):

    """
    Expected input:
    [
        {
            "features": [0.1, 0.2, 0.3],
            "label": 1
        }
    ]
    """

    return run_backtest(dataset)
