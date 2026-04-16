import math


# =========================
# ODDS → PROBABILITY (FIXED)
# =========================
def odds_to_prob(odds: float) -> float:
    if not odds or odds <= 0:
        return 0.0
    return 1.0 / float(odds)


# =========================
# NORMALIZE (REMOVE VIG)
# =========================
def normalize(home, draw, away):
    total = home + draw + away

    if total <= 0:
        return 0.33, 0.34, 0.33

    return home / total, draw / total, away / total


# =========================
# MARKET STRENGTH (STABLE LOG-RATIO)
# =========================
def market_strength(home_odds: float, away_odds: float):
    try:
        ratio = (away_odds + 1e-6) / (home_odds + 1e-6)

        # squash into stable range
        strength = math.tanh(math.log(ratio))

        return strength, -strength

    except Exception:
        return 0.0, 0.0


# =========================
# IMPLIED xG (NORMALIZED + SMART)
# =========================
def implied_xg(home_prob: float, away_prob: float):
    base_goals = 2.7

    total = home_prob + away_prob
    if total == 0:
        return 1.35, 1.35

    # normalize dominance
    h_share = home_prob / total
    a_share = away_prob / total

    # nonlinear scaling
    home_xg = base_goals * (h_share ** 1.2)
    away_xg = base_goals * (a_share ** 1.2)

    return home_xg, away_xg


# =========================
# MARKET ENTROPY (FULL)
# =========================
def market_entropy(h, d, a):
    try:
        return -(
            h * math.log(h + 1e-9) +
            d * math.log(d + 1e-9) +
            a * math.log(a + 1e-9)
        )
    except Exception:
        return 0.0


# =========================
# FULL MARKET VECTOR (UPGRADED)
# =========================
def market_vector(home_odds, draw_odds, away_odds):

    # raw implied probs
    h = odds_to_prob(home_odds)
    d = odds_to_prob(draw_odds)
    a = odds_to_prob(away_odds)

    # remove bookmaker margin
    h, d, a = normalize(h, d, a)

    # strength signal
    strength_h, strength_a = market_strength(home_odds, away_odds)

    # expected goals
    xg_h, xg_a = implied_xg(h, a)

    return {
        "h": h,
        "d": d,
        "a": a,

        # core signals
        "strength_diff": strength_h,
        "xg_diff": xg_h - xg_a,

        # uncertainty
        "entropy": market_entropy(h, d, a),

        # extra useful features (NEW)
        "favorite_prob": max(h, a),
        "underdog_prob": min(h, a),
        "draw_bias": d
    }
