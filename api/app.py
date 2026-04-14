from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest
from features.real_features import build_real_features


# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("football-api")


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
# FEATURE VALIDATOR
# =========================
def validate_features(features):
    if not isinstance(features, list) or len(features) != 3:
        raise ValueError("Invalid feature vector length")

    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except Exception:
            cleaned.append(0.0)

    return cleaned


# =========================
# PREDICT
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    try:
        match_dict = data.match.dict()

        logger.info(f"Predict request: {match_dict}")

        features = await build_real_features(match_dict)

        # 🔥 SAFE FEATURE VALIDATION
        features = validate_features(features)

        prediction = predict(features)

        return {
            "status": "success",
            "input": match_dict,
            "features": features,
            "prediction": prediction
        }

    except Exception as e:
        logger.error(f"Predict error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# LIVE
# =========================
@app.get("/live")
async def live_predictions():

    try:
        results = await run_live_predictions()

        # 🔥 SAFETY GUARD
        if not isinstance(results, list):
            results = []

        return {
            "status": "success",
            "total": len(results),
            "data": results
        }

    except Exception as e:
        logger.error(f"Live error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# BACKTEST
# =========================
@app.post("/backtest")
async def backtest_endpoint(matches: List[Match]):

    try:
        dataset = []

        # 🔥 CLEAN INPUT DATA
        for m in matches:
            item = m.dict()

            # enforce numeric safety
            item["homeOdds"] = float(item.get("homeOdds") or 2.0)
            item["drawOdds"] = float(item.get("drawOdds") or 3.2)
            item["awayOdds"] = float(item.get("awayOdds") or 2.0)

            dataset.append(item)

        result = run_backtest(dataset)

        return {
            "status": "success",
            "matches": len(dataset),
            "result": result
        }

    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
