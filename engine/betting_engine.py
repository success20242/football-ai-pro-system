from data.odds_api import get_odds
from models.predict import predict


# =========================
# ODDS → IMPLIED PROBABILITY
# =========================
def odds_to_prob(odds: float):
    if not odds or odds <= 1:
        return 0
    return 1 / odds


# =========================
# NORMALIZE MARKET PROBS
# =========================
def normalize_probs(p_home, p_draw, p_away):
    total = p_home + p_draw + p_away
    if total == 0:
        return {"home": 0, "draw": 0, "away": 0}

    return {
        "home": p_home / total,
        "draw": p_draw / total,
        "away": p_away / total
    }


# =========================
# VALUE CALCULATION
# =========================
def calculate_value(model_prob, market_prob):
    return model_prob - market_prob


# =========================
# MAIN BETTING ENGINE
# =========================
async def run_betting_engine():

    odds_data = await get_odds()

    results = []

    for match in odds_data:

        try:
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0]["markets"][0]["outcomes"]

            # =========================
            # SAFE EXTRACTION
            # =========================
            home_odds = None
            away_odds = None
            draw_odds = None

            for o in outcomes:
                name = o.get("name", "").lower()

                if name in ["home", match.get("home_team", "").lower()]:
                    home_odds = o["price"]

                elif name in ["away", match.get("away_team", "").lower()]:
                    away_odds = o["price"]

                elif name in ["draw", "tie"]:
                    draw_odds = o["price"]

            if not home_odds or not away_odds:
                continue

            # =========================
            # MARKET PROBABILITIES
            # =========================
            market_home = odds_to_prob(home_odds)
            market_draw = odds_to_prob(draw_odds or 3.2)
            market_away = odds_to_prob(away_odds)

            market_probs = normalize_probs(
                market_home, market_draw, market_away
            )

            # =========================
            # REAL FEATURE PIPELINE (NO FAKE INPUTS)
            # =========================
            features = [
                market_probs["home"],
                market_probs["away"],
                market_probs["home"] - market_probs["away"]
            ]

            model_probs = predict(features)

            # =========================
            # VALUE CALCULATION
            # =========================
            value_home = calculate_value(model_probs["home_win"], market_probs["home"])
            value_draw = calculate_value(model_probs["draw"], market_probs["draw"])
            value_away = calculate_value(model_probs["away_win"], market_probs["away"])

            best_bet = max(
                [("HOME", value_home),
                 ("DRAW", value_draw),
                 ("AWAY", value_away)],
                key=lambda x: x[1]
            )

            results.append({
                "home": match.get("home_team"),
                "away": match.get("away_team"),
                "best_bet": best_bet[0],
                "value": float(best_bet[1]),
                "model_probs": model_probs,
                "market_probs": market_probs
            })

        except Exception:
            continue

    return results
