def calculate_ev(probability: float, odds: float, confidence: float = 1.0) -> float:
    """
    Expected Value (calibrated version)

    Adds confidence weighting to reduce false positives
    """

    if not probability or not odds:
        return -1.0

    base_ev = (probability * odds) - 1

    # confidence dampening (critical upgrade)
    adjusted_ev = base_ev * confidence

    return round(adjusted_ev, 5)


# =========================
# DYNAMIC BET SIGNAL ENGINE
# =========================
def get_bet_signal(ev: float, probability: float = 0.0, confidence: float = 1.0) -> str:

    # confidence-adjusted thresholds
    confidence_factor = (probability * confidence)

    # dynamic scaling (prevents overbetting weak models)
    if ev < 0:
        return "NO_BET"

    if confidence_factor < 0.35:
        return "NO_BET"

    if ev < 0.03:
        return "WEAK_EDGE"

    if ev < 0.08:
        return "BET"

    return "STRONG_BET"
