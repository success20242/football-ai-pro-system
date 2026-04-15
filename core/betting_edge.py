def calculate_ev(probability: float, odds: float) -> float:
    """
    Expected Value for decimal odds
    """
    if not probability or not odds:
        return -1.0

    return (probability * odds) - 1


def get_bet_signal(ev: float) -> str:
    if ev < 0:
        return "NO_BET"
    elif ev < 0.05:
        return "WEAK_EDGE"
    elif ev < 0.10:
        return "BET"
    else:
        return "STRONG_BET"
