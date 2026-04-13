import asyncio
import random

from data.football_api import get_live_matches
from models.predict import predict


# =========================
# FEATURE ENGINE (NO CSV)
# =========================
def build_real_features(match):
    """
    Real-time feature generation (API-driven, no dataset dependency)
    """

    # Team names
    home_team = match["homeTeam"]["name"]
    away_team = match["awayTeam"]["name"]

    # -------------------------
    # SIMULATED BUT STRUCTURED SIGNALS
    # (replace later with real xG / stats API)
    # -------------------------

    home_attack_strength = random.uniform(0.8, 2.2)
    away_attack_strength = random.uniform(0.8, 2.2)

    home_defense_weakness = random.uniform(0.8, 2.0)
    away_defense_weakness = random.uniform(0.8, 2.0)

    # ⚽ FORM METRIC
    home_form = home_attack_strength - home_defense_weakness
    away_form = away_attack_strength - away_defense_weakness

    # 🧠 MOMENTUM (relative strength)
    momentum = home_form - away_form

    # 💰 MARKET EDGE PROXY
    market_edge = momentum * 0.2

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]


# =========================
# LIVE PREDICTIONS ENGINE
# =========================
async def run_live_predictions():

    data = await get_live_matches()
    matches = data.get("matches", [])

    results = []

    for match in matches:
        try:
            features = build_real_features(match)
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
