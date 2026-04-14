from data.odds_api import get_odds
from models.predict import predict


def odds_to_prob(odds: float):
    return 1 / odds if odds > 1 else 0


def kelly(prob, odds):
    if odds <= 1:
        return 0

    b = odds - 1
    q = 1 - prob

    f = (b * prob - q) / b
    return max(0, min(f, 0.25))


def calc_edge(model_prob, market_prob):
    return model_prob - market_prob


async def run_institutional_engine():

    odds_data = await get_odds()
    results = []

    for match in odds_data:

        try:
            home = match.get("home_team", "HOME")
            away = match.get("away_team", "AWAY")

            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0]["markets"][0]["outcomes"]

            def find_odds(name):
                for o in outcomes:
                    if o["name"] == name:
                        return o["price"]
                return None

            home_odds = find_odds(home)
            away_odds = find_odds(away)
            draw_odds = find_odds("Draw")

            if not all([home_odds, away_odds, draw_odds]):
                continue

            market_probs = {
                "home": odds_to_prob(home_odds),
                "draw": odds_to_prob(draw_odds),
                "away": odds_to_prob(away_odds)
            }

            total = sum(market_probs.values())
            market_probs = {k: v / total for k, v in market_probs.items()}

            model = predict([0.5, 0.5, 0.0])

            model_probs = {
                "home": model["home_win"],
                "draw": model["draw"],
                "away": model["away_win"]
            }

            edges = {
                k: calc_edge(model_probs[k], market_probs[k])
                for k in model_probs
            }

            best_key = max(edges, key=edges.get)

            odds_map = {
                "home": home_odds,
                "draw": draw_odds,
                "away": away_odds
            }

            stake = kelly(model_probs[best_key], odds_map[best_key])

            results.append({
                "match": f"{home} vs {away}",
                "best_bet": best_key.upper(),
                "edge": edges[best_key],
                "odds": odds_map[best_key],
                "stake": stake
            })

        except Exception:
            continue

    return results
