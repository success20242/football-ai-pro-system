import math

# =========================
# ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float) -> float:
    if not odds or odds <= 1:
        return 0.0
    return 1.0 / float(odds)


def normalize(home, draw, away):
    total = home + draw + away
    if total == 0:
        return 0.33, 0.34, 0.33

    return home / total, draw / total, away / total


# =========================
# MARKET IMPLIED TEAM STRENGTH
# =========================
def market_strength(home_odds: float, away_odds: float):
    """
    Stronger teams = lower odds = higher strength
    """
    home_strength = -math.log(home_odds)
    away_strength = -math.log(away_odds)

    return home_strength, away_strength


# =========================
# MARKET IMPLIED xG (KEY INNOVATION)
# =========================
def implied_xg(home_prob: float, away_prob: float):
    """
    Convert probabilities into goal expectation space
    """
    base_goals = 2.6  # global football average

    home_xg = base_goals * home_prob
    away_xg = base_goals * away_prob

    return home_xg, away_xg
