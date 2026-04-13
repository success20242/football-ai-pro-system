import asyncio

from data.football_api import get_live_matches
from models.predict import predict
from features.real_features import build_real_features


# =========================
# LIVE PREDICTIONS ENGINE
# =========================
async def run_live_predictions():

    data = await get_live_matches()
    matches = data.get("matches", [])

    results = []

    for match in matches:
        try:

            # ⚽ REAL FEATURE ENGINE (xG + odds + injuries)
            features = await build_real_features(match)

            # 🧠 MODEL PREDICTION
            prediction = predict(features)

            results.append({
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "prediction": prediction
            })

        except Exception:
            continue

    return results


# =========================
# DEBUG MODE
# =========================
if __name__ == "__main__":
    predictions = asyncio.run(run_live_predictions())
    print(predictions)
