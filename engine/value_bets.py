from core.config import Config


# =========================
# SAFE IMPLIED PROBABILITY
# =========================
def market_prob(odds):

    try:
        if not odds or odds <= 1:
            return 0.0
        return 1.0 / float(odds)
    except Exception:
        return 0.0


# =========================
# NORMALIZED VALUE CHECK
# =========================
def is_value(model_prob, odds):

    try:
        if not odds or odds <= 1:
            return False

        m_prob = market_prob(odds)

        # edge
        edge = model_prob - m_prob

        return edge > Config.VALUE_THRESHOLD

    except Exception:
        return False


# =========================
# ADVANCED VALUE SCORE (NEW)
# =========================
def value_score(model_prob, odds):

    """
    Institutional-grade value metric:
    combines edge + odds quality weighting
    """

    try:
        if not odds or odds <= 1:
            return 0.0

        m_prob = market_prob(odds)

        edge = model_prob - m_prob

        # odds weighting (higher odds = higher uncertainty)
        weight = min(1.5, max(0.5, odds / 2))

        return edge * weight

    except Exception:
        return 0.0


# =========================
# MULTI-OUTCOME VALUE FILTER
# =========================
def best_value_bet(model_probs: dict, odds: dict):

    """
    Returns best EV outcome across 1X2 market
    """

    try:
        candidates = []

        for key in ["home", "draw", "away"]:
            if key not in model_probs or key not in odds:
                continue

            score = value_score(model_probs[key], odds[key])

            candidates.append((key, score))

        if not candidates:
            return None

        best = max(candidates, key=lambda x: x[1])

        return best if best[1] > Config.VALUE_THRESHOLD else None

    except Exception:
        return None
