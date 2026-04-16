from engine.portfolio import Portfolio
from models.predict import predict


# =========================
# SAFE PROB NORMALIZATION
# =========================
def normalize_probs(probs: dict):

    cleaned = {
        "home": float(probs.get("home", 0.0)),
        "draw": float(probs.get("draw", 0.0)),
        "away": float(probs.get("away", 0.0))
    }

    total = sum(cleaned.values())

    if total <= 0:
        return {"home": 0.33, "draw": 0.34, "away": 0.33}

    return {k: v / total for k, v in cleaned.items()}


# =========================
# EXPECTED VALUE
# =========================
def expected_value(prob, odds):
    try:
        return (float(prob) * float(odds)) - 1
    except Exception:
        return -1


# =========================
# MAIN BACKTEST ENGINE (FIXED)
# =========================
def run_backtest(matches: list):

    portfolio = Portfolio(bankroll=1000)

    for match in matches:

        try:
            # -------------------------
            # FEATURE VECTOR
            # -------------------------
            features = [
                float(match.get("home_form", 0)),
                float(match.get("away_form", 0)),
                float(match.get("market_edge", 0))
            ]

            # -------------------------
            # PREDICTION
            # -------------------------
            prediction = predict(features)

            if not isinstance(prediction, dict):
                continue

            probs = prediction.get("probs", {})

            probs = {
                "home": max(0.0, min(probs.get("home", 0), 1.0)),
                "draw": max(0.0, min(probs.get("draw", 0), 1.0)),
                "away": max(0.0, min(probs.get("away", 0), 1.0))
            }

            probs = normalize_probs(probs)

            # -------------------------
            # BET SETUP
            # -------------------------
            bets = [
                ("HOME", probs["home"], match.get("homeOdds", 2.0)),
                ("DRAW", probs["draw"], match.get("drawOdds", 3.2)),
                ("AWAY", probs["away"], match.get("awayOdds", 2.0)),
            ]

            scored = [
                (b, expected_value(p, o), p, o)
                for b, p, o in bets
            ]

            # -------------------------
            # MULTI-EDGE FILTER (IMPORTANT FIX)
            # -------------------------
            valid_bets = [s for s in scored if s[1] > 0]

            if not valid_bets:
                continue

            # best EV bet
            bet_type, ev, prob, odds = max(valid_bets, key=lambda x: x[1])

            # -------------------------
            # KELLY STAKING (SAFE CAP)
            # -------------------------
            stake = portfolio.kelly_stake(prob, odds)
            stake = min(stake, portfolio.bankroll * 0.05)

            if stake <= 0:
                continue

            # -------------------------
            # RESULT CHECK
            # -------------------------
            result_map = {0: "HOME", 1: "DRAW", 2: "AWAY"}
            actual = result_map.get(match.get("result"))

            won = actual == bet_type

            portfolio.update(stake, odds, won)

        except Exception:
            continue

    return {
        "final_bankroll": float(portfolio.bankroll),
        "roi": float(portfolio.roi()),
        "history": portfolio.history
    }
