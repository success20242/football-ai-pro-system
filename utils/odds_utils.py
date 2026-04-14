# utils/odds_utils.py

def odds_to_prob(odds: float) -> float:
    """
    Convert decimal odds → implied probability
    """
    if not odds or odds <= 1:
        return 0.0
    return 1.0 / float(odds)


def normalize_probs(home: float, draw: float, away: float):
    """
    Normalize probabilities to remove bookmaker margin
    """
    total = home + draw + away

    if total == 0:
        return {"home": 0, "draw": 0, "away": 0}

    return {
        "home": home / total,
        "draw": draw / total,
        "away": away / total
    }


def extract_match_probs(match_odds: dict):
    """
    Convert API odds response → clean probability structure
    """

    try:
        bookmakers = match_odds.get("bookmakers", [])
        if not bookmakers:
            return None

        outcomes = bookmakers[0]["markets"][0]["outcomes"]

        home = next(o["price"] for o in outcomes if o.get("name") != "Draw" and "home" in o.get("name", "").lower())
        away = next(o["price"] for o in outcomes if o.get("name") != "Draw" and "away" in o.get("name", "").lower())
        draw = next(o["price"] for o in outcomes if o.get("name") == "Draw")

        probs = {
            "home": odds_to_prob(home),
            "draw": odds_to_prob(draw),
            "away": odds_to_prob(away),
        }

        return normalize_probs(**probs)

    except Exception:
        return None


def build_odds_map(odds_list: list):
    """
    SAFE mapping: match_id → odds object
    FIXES circular import & engine dependency issues
    """

    odds_map = {}

    for o in odds_list:
        match_id = o.get("id")
        if match_id:
            odds_map[match_id] = o

    return odds_map
