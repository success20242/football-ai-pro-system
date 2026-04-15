from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from models.predict import predict
from engine.backtest import run_backtest
from core.queue import enqueue_prediction

# 🔥 NEW IMPORTS
from data.odds_api import get_odds
from features.real_features import build_real_features

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("football-api")

app = FastAPI(title="Football Prediction API", version="4.0")


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
        "version": "4.0",
        "endpoints": ["/predict", "/live", "/backtest", "/health"]
    }


# =========================
# HELPERS
# =========================
def safe_match_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}


def format_prediction(pred):
    """
    Convert raw model output into readable format
    """
    try:
        return {
            "prediction": pred.get("label"),
            "confidence": round(float(pred.get("confidence", 0.5)), 4),
            "probabilities": pred.get("probs", {})
        }
    except:
        return {
            "prediction": "UNKNOWN",
            "confidence": 0.0,
            "probabilities": {}
        }


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
# 🔥 PREDICT (HYBRID: INSTANT + QUEUE)
# =========================
@app.post("/predict")
async def predict_endpoint(data: MatchInput):

    try:
        match = safe_match_dict(data.match)

        logger.info(f"Predict request: {match}")

        # -------------------------
        # 🔥 GET ODDS
        # -------------------------
        odds_list = await get_odds()
        odds_map = {o["match_key"]: o for o in odds_list}

        # -------------------------
        # 🔥 BUILD FEATURES
        # -------------------------
        features = await build_real_features(match, odds_map)

        # -------------------------
        # 🔥 RUN MODEL (INSTANT)
        # -------------------------
        prediction = predict(features)

        # -------------------------
        # 🔥 ALSO QUEUE (ASYNC PIPELINE)
        # -------------------------
        await enqueue_prediction(match)

        return {
            "status": "success",
            "instant_prediction": format_prediction(prediction),
            "message": "Prediction returned + queued for processing"
        }

    except Exception as e:
        logger.error(f"Predict error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# =========================
# 🔥 LIVE (REAL PREDICTIONS)
# =========================
@app.get("/live")
async def live_predictions():

    try:
        from data.football_api import get_live_matches

        # -------------------------
        # GET MATCHES
        # -------------------------
        live_data = await get_live_matches()
        matches = live_data.get("matches", [])

        # -------------------------
        # GET ODDS
        # -------------------------
        odds_list = await get_odds()
        odds_map = {o["match_key"]: o for o in odds_list}

        results = []

        for match in matches:
            features = await build_real_features(match, odds_map)
            pred = predict(features)

            results.append({
                "match": match,
                "prediction": format_prediction(pred)
            })

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
