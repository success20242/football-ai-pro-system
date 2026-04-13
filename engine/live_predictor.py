import asyncio
import pandas as pd

from data.football_api import get_live_matches
from models.predict import predict
from features.real_features import build_real_features


# 📊 Load historical dataset (used for real feature calculation)
df = pd.read_csv("data/matches.csv")


async def run_live_predictions():

    data = await get_live_matches()
    matches = data.get("matches", [])

    results = []

    for match in matches:
        try:
            home_team = match["homeTeam"]["name"]
            away_team = match["awayTeam"]["name"]

            # 🔥 REAL FEATURES (replaces fake/random)
            features = build_real_features(df, home_team, away_team)

            prediction = predict(features)

            results.append({
                "home_team": home_team,
                "away_team": away_team,
                "prediction": prediction
            })

        except Exception as e:
            continue

    return results


if __name__ == "__main__":
    predictions = asyncio.run(run_live_predictions())
    print(predictions)
