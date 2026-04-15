from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.predict import predict
from engine.live_predictor import run_live_predictions
from engine.backtest import run_backtest
from core.queue import enqueue_prediction

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("football-api")

app = FastAPI(title="Football Prediction API", version="3.0")


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
        "version": "3.0",
        "endpoints": ["/predict", "/live", "/backtest", "/health"]
    }


# =========================
# SAFE MATCH CONVERTER
# =========================
def safe_match_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "football-api"
    }


# =========================
# PREDICT ENDPOINT (SYNC MODEL ONLY)
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    try:
        match_dict = safe_match_dict(data.match)

        logger.info(f"Predict request: {match_dict}")

        # 🔥 PUSH INTO QUEUE (NEW ARCHITECTURE)
        await enqueue_prediction(match_dict)

        return {
            "status": "queued",
            "message": "Match sent to prediction worker"
        }

    except Exception as e:
        logger.error(f"Predict error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# LIVE ENDPOINT (PRODUCER ONLY)
# =========================
@app.get("/live")
async def live_predictions():

    try:
        result = await run_live_predictions()

        return {
            "status": "success",
            "total": result.get("total", 0),
            "data": result.get("data", [])
        }

    except Exception as e:
        logger.error(f"Live error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# BACKTEST ENDPOINT
# =========================
@app.post("/backtest")
async def backtest_endpoint(matches: List[Match]):

    try:
        dataset = []

        for m in matches:
            item = safe_match_dict(m)

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
