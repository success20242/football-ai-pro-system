from data.odds_api import get_odds
from utils.odds_utils import extract_match_probs
from models.predict import predict


# =========================
# ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float):
    try:
        if not odds or odds <= 1:
            return 0.0
        return 1 / float(odds)
    except Exception:
        return 0.0


# =========================
# KELLY CRITERION (SAFE)
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
    return float(model_prob - market_prob)


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
            # MARKET PROBABILITY (FIXED PIPELINE)
            # -------------------------
            market = extract_match_probs(match)

            if not market:
                continue

            # -------------------------
            # MODEL INPUT (REALISTIC)
            # -------------------------
            # NOTE:
            # replace later with real feature pipeline
            features = [
                0.5,   # placeholder form_diff
                0.5,   # placeholder injury_diff
                0.0    # placeholder market_edge
            ]

            model = predict(features)

            model_probs = {
                "home": model["home_win"],
                "draw": model["draw"],
                "away": model["away_win"]
            }

            # -------------------------
            # EDGE CALCULATION
            # -------------------------
            edges = {
                k: calc_edge(model_probs[k], market[k])
                for k in model_probs
            }

            best_key = max(edges, key=edges.get)

            # -------------------------
            # ODDS SAFE EXTRACTION
            # -------------------------
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])

            odds_map = {"home": 2.0, "draw": 3.2, "away": 2.0}

            for o in outcomes:
                name = o.get("name", "").lower()
                price = o.get("price", 2.0)

                if "home" in name:
                    odds_map["home"] = price
                elif "away" in name:
                    odds_map["away"] = price
                elif "draw" in name:
                    odds_map["draw"] = price

            # -------------------------
            # KELLY STAKE
            # -------------------------
            stake = kelly(model_probs[best_key], odds_map[best_key])

            results.append({
                "match": match.get("id", "unknown"),
                "best_bet": best_key.upper(),
                "edge": edges[best_key],
                "odds": odds_map[best_key],
                "model_prob": model_probs[best_key],
                "market_prob": market[best_key],
                "stake": float(stake)
            })

        except Exception:
            continue

    return results
