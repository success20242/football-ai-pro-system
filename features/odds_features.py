import math


# =========================
# IMPLIED PROBABILITY
# =========================
def implied_prob(decimal_odds: float) -> float:
    if not decimal_odds or decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


# =========================
# NORMALIZE (REMOVE VIG)
# =========================
def normalize_probs(probs: dict) -> dict:
    total = sum(probs.values())

    if total == 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    return {k: v / total for k, v in probs.items()}


# =========================
# SAFE EXTRACTOR (FIXED)
# =========================
def extract_match_probs(odds_match: dict):

    try:
        bookmakers = odds_match.get("bookmakers", [])
        if not bookmakers:
            raise ValueError("No bookmakers")

        markets = bookmakers[0].get("markets", [])
        if not markets:
            raise ValueError("No markets")

        outcomes = markets[0].get("outcomes", [])
        if not outcomes:
            raise ValueError("No outcomes")

        raw = {
            "home": 0.0,
            "draw": 0.0,
            "away": 0.0
        }

        # -------------------------
        # SMART DETECTION
        # -------------------------
        for o in outcomes:
            name = o.get("name", "").lower()
            price = o.get("price", 0)

            prob = implied_prob(price)

            # detect draw
            if "draw" in name:
                raw["draw"] = prob

            # detect home/away by position fallback
            elif raw["home"] == 0:
                raw["home"] = prob
            else:
                raw["away"] = prob

        return normalize_probs(raw)

    except Exception as e:
        print(f"⚠️ ODDS PARSE ERROR → {e}")

        # SAFE fallback (prevents identical predictions issue)
        return {
            "home": 0.33,
            "draw": 0.34,
            "away": 0.33
        }
