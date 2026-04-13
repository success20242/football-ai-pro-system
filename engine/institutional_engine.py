import math
from data.odds_api import get_odds
from models.predict import predict


# =========================
# ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float):
    if odds <= 1:
        return 0
    return 1 / odds


# =========================
# KELLY CRITERION (RISK SIZING)
# =========================
def kelly(prob, odds):
    if odds <= 1:
        return 0

    b = odds - 1
    q = 1 - prob

    f = (b * prob - q) / b

    return max(0, min(f, 0.25))  # cap risk at 25% bankroll


# =========================
# EDGE CALCULATION
# =========================
def calc_edge(model_prob, market_prob):
    return model_prob - market_prob


# =========================
# MAIN INSTITUTIONAL ENGINE
# =========================
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

            home_odds = next(o["price"] for o in outcomes if o["name"] == home)
            away_odds = next(o["price"] for o in outcomes if o["name"] == away)
            draw_odds = next(o["price"] for o in outcomes if o["name"] == "Draw")

            # -------------------------
            # MARKET PROBABILITIES
            # -------------------------
            market_home = odds_to_prob(home_odds)
            market_away = odds_to_prob(away_odds)
            market_draw = odds_to_prob(draw_odds)

            # normalize (important)
            total = market_home + market_draw + market_away

            market_probs = {
                "home": market_home / total,
                "draw": market_draw / total,
                "away": market_away / total
            }

            # -------------------------
            # MODEL PREDICTION (REAL FEATURES LATER)
            # -------------------------
            features = [0.5, 0.5, 0.0]  # placeholder until API-linked features
            model = predict(features)

            model_probs = {
                "home": model["home_win"],
                "draw": model["draw"],
                "away": model["away_win"]
            }

            # -------------------------
            # EDGE CALCULATION
            # -------------------------
            edge_home = calc_edge(model_probs["home"], market_probs["home"])
            edge_draw = calc_edge(model_probs["draw"], market_probs["draw"])
            edge_away = calc_edge(model_probs["away"], market_probs["away"])

            # -------------------------
            # BEST BET
            # -------------------------
            best = max(
                [("HOME", edge_home, home_odds, model_probs["home"]),
                 ("DRAW", edge_draw, draw_odds, model_probs["draw"]),
                 ("AWAY", edge_away, away_odds, model_probs["away"])],
                key=lambda x: x[1]
            )

            # -------------------------
            # KELLY STAKING
            # -------------------------
            stake = kelly(best[3], best[2])

            results.append({
                "match": f"{home} vs {away}",
                "best_bet": best[0],
                "edge": float(best[1]),
                "odds": best[2],
                "model_prob": best[3],
                "market_probs": market_probs,
                "stake_fraction": float(stake)
            })

        except Exception:
            continue

    return results
