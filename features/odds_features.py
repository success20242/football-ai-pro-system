import math

def implied_prob(decimal_odds: float) -> float:
    """
    Convert bookmaker odds → implied probability
    (before normalization)
    """
    if decimal_odds <= 0:
        return 0.0
    return 1.0 / decimal_odds


def normalize_probs(probs: dict) -> dict:
    """
    Remove bookmaker margin (vig)
    """
    total = sum(probs.values())
    return {k: v / total for k, v in probs.items()}


def extract_match_probs(odds_match: dict):
    """
    Convert raw API odds → clean probability structure
    """

    outcomes = odds_match.get("bookmakers", [])[0]["markets"][0]["outcomes"]

    raw = {
        "home": 0,
        "draw": 0,
        "away": 0
    }

    for o in outcomes:
        name = o["name"].lower()
        prob = implied_prob(o["price"])

        if "home" in name:
            raw["home"] = prob
        elif "draw" in name:
            raw["draw"] = prob
        else:
            raw["away"] = prob

    return normalize_probs(raw)
