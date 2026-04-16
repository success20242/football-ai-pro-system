import math


# =========================
# xG FEATURE ENGINE (IMPROVED PROXY)
# =========================
def compute_xg_proxy(team_stats: dict):

    """
    Lightweight but stable proxy until real xG API is integrated.
    Designed to NOT distort ML signals.
    """

    if not isinstance(team_stats, dict):
        return {"xg_for": 1.0, "xg_against": 1.0}

    stats = team_stats.get("statistics", {})

    # safe defaults
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    draws = stats.get("draws", 0)
    played = wins + losses + draws

    if played == 0:
        return {"xg_for": 1.0, "xg_against": 1.0}

    # performance ratio (stable proxy signal)
    win_rate = wins / played
    loss_rate = losses / played
    draw_rate = draws / played

    # attack proxy: weighted performance
    attack_strength = (win_rate * 1.6) + (draw_rate * 0.8)

    # defense proxy: inverse pressure
    defense_strength = (loss_rate * 1.4) + (draw_rate * 0.6)

    # normalize to football scale
    xg_for = 1.2 + attack_strength * 1.8
    xg_against = 1.2 + defense_strength * 1.6

    return {
        "xg_for": round(float(xg_for), 4),
        "xg_against": round(float(xg_against), 4)
    }


# =========================
# xG DIFFERENCE FEATURE
# =========================
def build_team_strength(home_xg, away_xg):

    """
    Converts xG into stable ML-ready signal
    """

    home_attack = home_xg.get("xg_for", 1.0)
    home_defense = home_xg.get("xg_against", 1.0)

    away_attack = away_xg.get("xg_for", 1.0)
    away_defense = away_xg.get("xg_against", 1.0)

    home_form = home_attack - home_defense
    away_form = away_attack - away_defense

    # normalized difference (VERY IMPORTANT)
    diff = home_form - away_form

    # squash for ML stability
    return home_form, away_form, math.tanh(diff)
