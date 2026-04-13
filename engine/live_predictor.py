import asyncio
import random

from data.football_api import get_live_matches
from models.predict import predict


def build_live_features(match):
    """
    Simulated realistic football features (temporary)
    """

    # ⚽ simulate attacking strength
    home_goals_avg = random.uniform(0.8, 2.2)
    away_goals_avg = random.uniform(0.8, 2.2)

    # 🛡️ simulate defensive weakness
    home_concede_avg = random.uniform(0.8, 2.0)
    away_concede_avg = random.uniform(0.8, 2.0)

    # 📊 form proxy (attack - defense)
    home_form = home_goals_avg - home_concede_avg
    away_form = away_goals_avg - away_concede_avg

    # 🧠 momentum (relative strength)
    momentum = home_form - away_form

    # 💰 market edge proxy
    market_edge = momentum * 0.2

    return [
        float(home_form),
        float(away_form),
        float(market_edge)
    ]


async def run_live_predictions():

    data = await get_live_matches()
    matches = data.get("matches", [])

    results = []

    for match in matches:
        try:
            features = build_live_features(match)
            prediction = predict(features)

            results.append({
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "prediction": prediction
            })

        except Exception as e:
            continue

    return results


if __name__ == "__main__":
    predictions = asyncio.run(run_live_predictions())
    print(predictions)
