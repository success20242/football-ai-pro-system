from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest
from features.real_features import build_real_features

app = FastAPI(title="Football Prediction API", version="2.0")


# =========================
# SCHEMAS
# =========================
class Match(BaseModel):
    homeTeam: str = Field(..., example="Arsenal")
    awayTeam: str = Field(..., example="Chelsea")

    homeOdds: Optional[float] = Field(None, example=2.1)
    drawOdds: Optional[float] = Field(None, example=3.4)
    awayOdds: Optional[float] = Field(None, example=3.2)

    league: Optional[str] = Field(None, example="EPL")
    timestamp: Optional[datetime] = None


class MatchInput(BaseModel):
    match: Match


# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Football Prediction API running 🚀",
        "endpoints": ["/predict", "/live", "/backtest"]
    }


# =========================
# PREDICT
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):
    try:
        match_dict = data.match.dict()

        features = await build_real_features(match_dict)
        prediction = predict(features)

        return {
            "status": "success",
            "input": match_dict,
            "prediction": prediction
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# LIVE
# =========================
@app.get("/live")
async def live_predictions():
    try:
        results = await run_live_predictions()

        return {
            "status": "success",
            "total": len(results),
            "data": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# BACKTEST
# =========================
@app.post("/backtest")
async def backtest_endpoint(matches: List[Match]):
    try:
        dataset = [m.dict() for m in matches]
        result = run_backtest(dataset)

        return {
            "status": "success",
            "matches": len(dataset),
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
