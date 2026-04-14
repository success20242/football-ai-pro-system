from features.market_model import (
    odds_to_prob,
    normalize,
    market_strength,
    implied_xg
)

# =========================
# FEATURE ENGINE (FINAL)
# =========================
async def build_real_features(match, odds_map=None):

    match_id = match.get("id")

    odds = {}
    if odds_map and match_id in odds_map:
        odds = odds_map[match_id]

    home_odds = odds.get("home", 2.0)
    draw_odds = odds.get("draw", 3.2)
    away_odds = odds.get("away", 2.0)

    # =========================
    # IMPLIED PROBABILITY
    # =========================
    home_p = odds_to_prob(home_odds)
    draw_p = odds_to_prob(draw_odds)
    away_p = odds_to_prob(away_odds)

    home_p, draw_p, away_p = normalize(home_p, draw_p, away_p)

    # =========================
    # MARKET STRENGTH (ELO-LIKE)
    # =========================
    home_strength, away_strength = market_strength(home_odds, away_odds)

    # =========================
    # IMPLIED xG
    # =========================
    home_xg, away_xg = implied_xg(home_p, away_p)

    # =========================
    # CORE SIGNALS
    # =========================
    strength_diff = home_strength - away_strength
    xg_diff = home_xg - away_xg
    market_bias = home_p - away_p

    # =========================
    # FINAL FEATURE VECTOR
    # =========================
    return [
        float(strength_diff),
        float(xg_diff),
        float(market_bias)
    ]
