from fastapi import FastAPI
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest

app = FastAPI()


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


@app.get("/live")
async def live_predictions():
    return await run_live_predictions()


# 🟢 NEW: BACKTEST ENDPOINT
@app.post("/backtest")
def backtest_endpoint(dataset: list):

    import pandas as pd

    df = pd.DataFrame(dataset)

    return run_backtest(df)
