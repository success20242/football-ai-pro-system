import math


# =========================
# ODDS → PROBABILITY
# =========================
def odds_to_prob(odds: float) -> float:
    if not odds or odds <= 1:
        return 0.0
    return 1.0 / float(odds)


# =========================
# NORMALIZE (REMOVE VIG)
# =========================
def normalize(home, draw, away):
    total = home + draw + away
    if total == 0:
        return 0.33, 0.34, 0.33

    return home / total, draw / total, away / total


# =========================
# ELO-LIKE MARKET STRENGTH
# =========================
def market_strength(home_odds: float, away_odds: float):
    home_strength = math.log((away_odds + 1e-6) / (home_odds + 1e-6))
    away_strength = -home_strength
    return home_strength, away_strength


# =========================
# IMPLIED xG (MARKET ANCHORED)
# =========================
def implied_xg(home_prob: float, away_prob: float):
    base_goals = 2.7

    # nonlinear scaling (IMPORTANT UPGRADE)
    home_xg = base_goals * (home_prob ** 1.15)
    away_xg = base_goals * (away_prob ** 1.15)

    return home_xg, away_xg


# =========================
# FULL MARKET VECTOR
# =========================
def market_vector(home_odds, draw_odds, away_odds):
    h = odds_to_prob(home_odds)
    d = odds_to_prob(draw_odds)
    a = odds_to_prob(away_odds)

    h, d, a = normalize(h, d, a)

    strength_h, strength_a = market_strength(home_odds, away_odds)
    xg_h, xg_a = implied_xg(h, a)

    return {
        "h": h,
        "d": d,
        "a": a,
        "strength_diff": strength_h,
        "xg_diff": xg_h - xg_a,
        "market_entropy": -(h*math.log(h+1e-6) + a*math.log(a+1e-6))
    }
