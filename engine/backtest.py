from engine.portfolio import Portfolio
from models.predict import predict


# =========================
# SAFE PROB NORMALIZATION
# =========================
def normalize_probs(probs: dict):

    required = ["home_win", "draw", "away_win"]

    cleaned = {
        k: float(probs.get(k, 0.0))
        for k in required
    }

    total = sum(cleaned.values())

    if total <= 0:
        return {
            "home_win": 0.33,
            "draw": 0.34,
            "away_win": 0.33
        }

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
# MAIN BACKTEST ENGINE
# =========================
def run_backtest(matches: list):

    portfolio = Portfolio(bankroll=1000)

    for match in matches:

        try:
            # -------------------------
            # FEATURE VECTOR (SAFE)
            # -------------------------
            features = [
                float(match.get("home_form", 0)),
                float(match.get("away_form", 0)),
                float(match.get("market_edge", 0))
            ]

            raw_probs = predict(features)

            # -------------------------
            # SAFETY CLAMP (IMPORTANT)
            # prevents model explosion
            # -------------------------
            probs = {
                "home_win": max(0.0, min(raw_probs.get("home_win", 0), 1.0)),
                "draw": max(0.0, min(raw_probs.get("draw", 0), 1.0)),
                "away_win": max(0.0, min(raw_probs.get("away_win", 0), 1.0))
            }

            probs = normalize_probs(probs)

            # -------------------------
            # BET SETUP
            # -------------------------
            bets = [
                ("HOME", probs["home_win"], match.get("homeOdds", 2.0)),
                ("DRAW", probs["draw"], match.get("drawOdds", 3.2)),
                ("AWAY", probs["away_win"], match.get("awayOdds", 2.0)),
            ]

            scored = [
                (b, expected_value(p, o), p, o)
                for b, p, o in bets
            ]

            best = max(scored, key=lambda x: x[1])

            bet_type, ev, prob, odds = best

            # -------------------------
            # KELLY STAKING (SAFE CAP)
            # -------------------------
            stake = portfolio.kelly_stake(prob, odds)
            stake = min(stake, portfolio.bankroll * 0.05)

            # skip bad bets
            if stake <= 0 or ev <= 0:
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
