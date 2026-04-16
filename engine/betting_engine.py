from data.odds_api import get_odds
from models.predict import predict


# =========================
# ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float):
    if not odds or odds <= 1:
        return 0.0
    return 1 / odds


# =========================
# NORMALIZE MARKET PROBS
# =========================
def normalize_probs(p_home, p_draw, p_away):
    total = p_home + p_draw + p_away

    if total <= 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    return {
        "home": p_home / total,
        "draw": p_draw / total,
        "away": p_away / total
    }


# =========================
# VALUE CALCULATION
# =========================
def calculate_value(model_prob, market_prob):
    return float(model_prob) - float(market_prob)


# =========================
# SAFE ODDS EXTRACTION
# =========================
def extract_odds(outcomes):

    home = draw = away = None

    for o in outcomes:

        name = str(o.get("name", "")).lower()
        price = o.get("price")

        if not price:
            continue

        if "draw" in name or "tie" in name:
            draw = price
        elif home is None:
            home = price
        elif away is None:
            away = price

    return home, draw, away


# =========================
# MAIN BETTING ENGINE (FIXED)
# =========================
async def run_betting_engine():

    odds_data = await get_odds()
    results = []

    for match in odds_data:

        try:
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0].get("markets", [])[0].get("outcomes", [])
            if not outcomes:
                continue

            home_odds, draw_odds, away_odds = extract_odds(outcomes)

            if not home_odds or not away_odds:
                continue

            # -------------------------
            # MARKET PROBABILITIES
            # -------------------------
            market_home = odds_to_prob(home_odds)
            market_draw = odds_to_prob(draw_odds or 3.2)
            market_away = odds_to_prob(away_odds)

            market_probs = normalize_probs(
                market_home, market_draw, market_away
            )

            # -------------------------
            # FEATURE VECTOR (FIXED)
            # USE YOUR REAL SIGNALS (NOT MARKET)
            # -------------------------
            features = [
                market_probs["home"] - market_probs["away"],  # proxy imbalance
                market_probs["home"],
                market_probs["away"]
            ]

            prediction = predict(features)

            if not isinstance(prediction, dict):
                continue

            model_probs = prediction.get("probs", {})

            # -------------------------
            # VALUE CALCULATION (SAFE)
            # -------------------------
            value_home = calculate_value(
                model_probs.get("home", 0),
                market_probs["home"]
            )

            value_draw = calculate_value(
                model_probs.get("draw", 0),
                market_probs["draw"]
            )

            value_away = calculate_value(
                model_probs.get("away", 0),
                market_probs["away"]
            )

            # -------------------------
            # BEST POSITIVE EV ONLY
            # -------------------------
            candidates = [
                ("HOME", value_home),
                ("DRAW", value_draw),
                ("AWAY", value_away)
            ]

            best_bet = max(candidates, key=lambda x: x[1])

            if best_bet[1] <= 0:
                continue

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
