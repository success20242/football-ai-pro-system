# =========================
# xG FEATURE ENGINE
# =========================

def compute_xg_proxy(team_stats: dict):
    """
    Placeholder until you plug:
    - Understat
    - API-Football xG feed
    - StatsBomb (best option)
    """

    squad = team_stats.get("squad", [])

    # weak proxy model (replace later)
    base_attack = len(squad) / 30
    base_defense = 1 - base_attack

    xg_for = base_attack * 1.5
    xg_against = base_defense * 1.2

    return {
        "xg_for": float(xg_for),
        "xg_against": float(xg_against)
    }


def build_team_strength(home_xg, away_xg):
    """
    Converts xG into model-ready signal
    """

    home_form = home_xg["xg_for"] - home_xg["xg_against"]
    away_form = away_xg["xg_for"] - away_xg["xg_against"]

    return home_form, away_form
