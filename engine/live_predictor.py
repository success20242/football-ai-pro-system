import asyncio
from data.football_api import get_live_matches
from models.predict import predict

def build_live_features(match):

    home_team = match["homeTeam"]["name"]
    away_team = match["awayTeam"]["name"]

    # 🔥 TEMP smarter logic (better than static)
    home_form = hash(home_team) % 100 / 100
    away_form = hash(away_team) % 100 / 100

    # simulate market difference
    market_edge = (home_form - away_form) * 0.1

    return [home_form, away_form, market_edge]


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
