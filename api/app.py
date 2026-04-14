from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest
from features.real_features import build_real_features

app = FastAPI()


class MatchInput(BaseModel):
    match: dict


# =========================
# REAL FEATURE PREDICTION
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    match = data.match

    # ✅ VALIDATION (CRITICAL FIX)
    if "homeTeam" not in match or "awayTeam" not in match:
        raise HTTPException(
            status_code=400,
            detail="Invalid match format. Must include homeTeam and awayTeam"
        )

    try:
        features = await build_real_features(match)
        return predict(features)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# LIVE
# =========================
@app.get("/live")
async def live_predictions():
    return await run_live_predictions()


# =========================
# BACKTEST
# =========================
@app.post("/backtest")
async def backtest_endpoint(dataset: list = Body(...)):

    import pandas as pd

    try:
        df = pd.DataFrame(dataset)
        return run_backtest(df)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
