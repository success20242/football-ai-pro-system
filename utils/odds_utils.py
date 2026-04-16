def odds_to_prob(odds: float) -> float:
    try:
        if not odds or odds <= 1:
            return 0.0
        return 1.0 / float(odds)
    except Exception:
        return 0.0


def normalize_probs(home: float, draw: float, away: float):
    total = home + draw + away

    if total <= 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    return {
        "home": home / total,
        "draw": draw / total,
        "away": away / total
    }


# =========================
# SAFE ODDS PARSER (FIXED)
# =========================
def extract_match_probs(match_odds: dict):

    try:
        if not isinstance(match_odds, dict):
            return {"home": 0.33, "draw": 0.34, "away": 0.33}

        bookmakers = match_odds.get("bookmakers", [])
        if not bookmakers:
            return {"home": 0.33, "draw": 0.34, "away": 0.33}

        markets = bookmakers[0].get("markets", [])
        if not markets:
            return {"home": 0.33, "draw": 0.34, "away": 0.33}

        outcomes = markets[0].get("outcomes", [])
        if not outcomes:
            return {"home": 0.33, "draw": 0.34, "away": 0.33}

        home_odds = None
        away_odds = None
        draw_odds = None

        # =========================
        # IMPROVED DETECTION LOGIC
        # =========================
        for o in outcomes:

            if not isinstance(o, dict):
                continue

            name = str(o.get("name", "")).lower()
            price = o.get("price", None)

            if not price:
                continue

            # draw detection
            if "draw" in name or "tie" in name:
                draw_odds = price

            # assign remaining as home/away safely
            elif home_odds is None:
                home_odds = price
            elif away_odds is None:
                away_odds = price

        # =========================
        # SAFETY FALLBACKS (IMPORTANT FIX)
        # =========================
        home_odds = float(home_odds) if home_odds else 2.0
        away_odds = float(away_odds) if away_odds else 2.0
        draw_odds = float(draw_odds) if draw_odds else 3.2

        # =========================
        # IMPLIED PROBABILITIES
        # =========================
        home_p = odds_to_prob(home_odds)
        draw_p = odds_to_prob(draw_odds)
        away_p = odds_to_prob(away_odds)

        # =========================
        # NORMALIZE
        # =========================
        return normalize_probs(home_p, draw_p, away_p)

    except Exception:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}


# =========================
# ODDS MAP BUILDER (SAFE)
# =========================
def build_odds_map(odds_list: list):

    odds_map = {}

    if not isinstance(odds_list, list):
        return odds_map

    for o in odds_list:

        if not isinstance(o, dict):
            continue

        match_id = o.get("id")

        if match_id is None:
            continue

        odds_map[match_id] = o

    return odds_map
