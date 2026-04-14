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


app = FastAPI(title="Football Prediction API", version="2.1")


# =========================
# SCHEMAS
# =========================
class Match(BaseModel):
    homeTeam: str = Field(..., example="Arsenal")
    awayTeam: str = Field(..., example="Chelsea")

    homeOdds: Optional[float] = None
    drawOdds: Optional[float] = None
    awayOdds: Optional[float] = None

    league: Optional[str] = None
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
# FEATURE NORMALIZER (IMPORTANT FIX)
# =========================
def normalize_features(features):
    """
    Ensures model stability across different feature versions
    """

    if not isinstance(features, list):
        return [0.0, 0.0, 0.0]

    # force numeric safety
    cleaned = []
    for f in features:
        try:
            cleaned.append(float(f))
        except:
            cleaned.append(0.0)

    # FIX: enforce exactly 5 dims (latest engine standard)
    while len(cleaned) < 5:
        cleaned.append(0.0)

    return cleaned[:5]


# =========================
# PREDICT
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    try:
        match_dict = data.match.dict()

        logger.info(f"Predict request: {match_dict}")

        features = await build_real_features(match_dict)

        features = normalize_features(features)

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

        # FIX: correct structure handling
        if isinstance(results, dict):
            data = results.get("data", [])
        else:
            data = []

        return {
            "status": "success",
            "total": len(data),
            "data": data
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

        for m in matches:
            item = m.dict()

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
