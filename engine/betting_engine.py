from data.odds_api import get_odds
from models.predict import predict


# =========================
# CONVERT ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float):
    if odds <= 0:
        return 0
    return 1 / odds


# =========================
# FIND VALUE BET
# =========================
def calculate_value(model_prob, market_prob):
    return model_prob - market_prob


# =========================
# MAIN ENGINE
# =========================
async def run_betting_engine():

    odds_data = await get_odds()

    results = []

    for match in odds_data:

        try:
            home = match["home_team"]
            away = match["away_team"]

            # ---- extract odds safely ----
            outcomes = match.get("bookmakers", [])[0]["markets"][0]["outcomes"]

            home_odds = next(o["price"] for o in outcomes if o["name"] == home)
            away_odds = next(o["price"] for o in outcomes if o["name"] == away)
            draw_odds = next(o["price"] for o in outcomes if o["name"] == "Draw")

            # ---- convert odds to probabilities ----
            market_home = odds_to_prob(home_odds)
            market_away = odds_to_prob(away_odds)
            market_draw = odds_to_prob(draw_odds)

            market_probs = {
                "home": market_home,
                "draw": market_draw,
                "away": market_away
            }

            # ---- fake features for now (replace later with real engine) ----
            features = [0.5, 0.5, 0.0]

            model_probs = predict(features)

            # ---- compute value ----
            value_home = calculate_value(model_probs["home_win"], market_home)
            value_draw = calculate_value(model_probs["draw"], market_draw)
            value_away = calculate_value(model_probs["away_win"], market_away)

            best_bet = max(
                [("HOME", value_home),
                 ("DRAW", value_draw),
                 ("AWAY", value_away)],
                key=lambda x: x[1]
            )

            results.append({
                "home": home,
                "away": away,
                "best_bet": best_bet[0],
                "value": float(best_bet[1]),
                "model_probs": model_probs,
                "market_probs": market_probs
            })

        except Exception:
            continue

    return results
