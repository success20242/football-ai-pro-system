from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# KELLY CRITERION (FIXED)
# =========================
def kelly(prob, odds):
    try:
        if odds <= 1:
            return 0

        b = odds - 1
        q = 1 - prob

        f = (b * prob - q) / b
        return max(0, min(f, 0.25))
    except Exception:
        return 0


# =========================
# EDGE CALCULATION
# =========================
def calc_edge(model_prob, market_prob):
    return float(model_prob) - float(market_prob)


# =========================
# SAFE ODDS PARSER
# =========================
def extract_odds_from_match(match):

    bookmakers = match.get("bookmakers", [])
    if not bookmakers:
        return {"home": 2.0, "draw": 3.2, "away": 2.0}

    outcomes = bookmakers[0].get("markets", [])[0].get("outcomes", [])

    odds = {"home": 2.0, "draw": 3.2, "away": 2.0}

    for o in outcomes:
        name = str(o.get("name", "")).lower()
        price = o.get("price", 2.0)

        if "home" in name:
            odds["home"] = price
        elif "away" in name:
            odds["away"] = price
        elif "draw" in name:
            odds["draw"] = price

    return odds


# =========================
# MAIN ENGINE (FIXED)
# =========================
async def run_institutional_engine():

    odds_data = await get_odds()
    results = []

    if not odds_data:
        return results

    for match in odds_data:

        try:
            # -------------------------
            # MARKET PROBABILITY
            # -------------------------
            market = extract_match_probs(match)

            if not market:
                continue

            # -------------------------
            # REAL MODEL INPUT (FIXED)
            # -------------------------
            features = [
                market["home"] - market["away"],  # proxy imbalance
                market["home"],
                market["away"]
            ]

            model = predict(features)

            if not isinstance(model, dict):
                continue

            model_probs = model.get("probs", {})

            if not model_probs:
                continue

            # -------------------------
            # MARKET ODDS
            # -------------------------
            odds_map = extract_odds_from_match(match)

            # -------------------------
            # EDGE CALCULATION
            # -------------------------
            edges = {
                "home": calc_edge(model_probs["home"], market["home"]),
                "draw": calc_edge(model_probs["draw"], market["draw"]),
                "away": calc_edge(model_probs["away"], market["away"]),
            }

            # -------------------------
            # FILTER NEGATIVE EDGES (IMPORTANT FIX)
            # -------------------------
            valid_edges = {k: v for k, v in edges.items() if v > 0}

            if not valid_edges:
                continue

            best_key = max(valid_edges, key=valid_edges.get)

            # -------------------------
            # KELLY STAKE (FIXED USAGE)
            # -------------------------
            stake_fraction = kelly(
                model_probs[best_key],
                odds_map[best_key]
            )

            results.append({
                "match": match.get("id", "unknown"),
                "best_bet": best_key.upper(),
                "edge": edges[best_key],
                "odds": odds_map[best_key],
                "model_prob": model_probs[best_key],
                "market_prob": market[best_key],
                "kelly_fraction": float(stake_fraction)
            })

        except Exception:
            continue

    return results
