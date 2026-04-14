# utils/odds_utils.py

def odds_to_prob(odds: float) -> float:
    """
    Convert decimal odds → implied probability
    """
    try:
        if not odds or odds <= 1:
            return 0.0
        return 1.0 / float(odds)
    except Exception:
        return 0.0


def normalize_probs(home: float, draw: float, away: float):
    """
    Remove bookmaker margin (vig)
    """
    total = home + draw + away

    if total <= 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    return {
        "home": home / total,
        "draw": draw / total,
        "away": away / total
    }


# =========================
# SAFE ODDS PARSER (FIXED)
# =========================
def extract_match_probs(match_odds: dict):

    try:
        bookmakers = match_odds.get("bookmakers", [])
        if not bookmakers:
            return None

        outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])
        if not outcomes:
            return None

        home_odds = None
        away_odds = None
        draw_odds = None

        # -------------------------
        # FLEXIBLE MATCHING LOGIC
        # -------------------------
        for o in outcomes:

            name = o.get("name", "").lower()
            price = o.get("price", 0)

            # HOME detection
            if "home" in name:
                home_odds = price

            # AWAY detection
            elif "away" in name:
                away_odds = price

            # DRAW detection
            elif "draw" in name or "tie" in name:
                draw_odds = price

        # -------------------------
        # FALLBACK SAFETY
        # -------------------------
        home_odds = home_odds or 2.0
        away_odds = away_odds or 2.0
        draw_odds = draw_odds or 3.2

        # -------------------------
        # CONVERT TO PROBABILITIES
        # -------------------------
        probs = {
            "home": odds_to_prob(home_odds),
            "draw": odds_to_prob(draw_odds),
            "away": odds_to_prob(away_odds),
        }

        return normalize_probs(**probs)

    except Exception:
        return None


# =========================
# ODDS MAP BUILDER (SAFE)
# =========================
def build_odds_map(odds_list: list):

    odds_map = {}

    if not isinstance(odds_list, list):
        return odds_map

    for o in odds_list:

        if not isinstance(o, dict):
            continue

        match_id = o.get("id")

        if match_id is None:
            continue

        odds_map[match_id] = o

    return odds_map
