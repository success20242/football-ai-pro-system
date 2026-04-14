import pandas as pd
from engine.portfolio import Portfolio
from models.predict import predict


def normalize_probs(probs):
    total = probs["home_win"] + probs["draw"] + probs["away_win"]

    if total == 0:
        return probs

    return {
        "home_win": probs["home_win"] / total,
        "draw": probs["draw"] / total,
        "away_win": probs["away_win"] / total,
    }


def expected_value(prob, odds):
    return (prob * odds) - 1


def run_backtest(df):

    portfolio = Portfolio(bankroll=1000)

    for _, row in df.iterrows():

        try:
            features = [
                float(row["home_form"]),
                float(row["away_form"]),
                float(row["market_edge"])
            ]

            probs = normalize_probs(predict(features))

            bets = [
                ("HOME", probs["home_win"], row.get("odds_home", 2.0)),
                ("DRAW", probs["draw"], row.get("odds_draw", 3.2)),
                ("AWAY", probs["away_win"], row.get("odds_away", 2.0)),
            ]

            scored = [
                (b, expected_value(p, o), p, o)
                for b, p, o in bets
            ]

            best = max(scored, key=lambda x: x[1])

            bet_type, ev, prob, odds = best

            stake = portfolio.kelly_stake(prob, odds)

            # 🔥 risk control
            stake = min(stake, portfolio.bankroll * 0.05)

            if stake <= 0 or ev <= 0:
                continue

            result_map = {0: "HOME", 1: "DRAW", 2: "AWAY"}

            won = (result_map.get(row["result"]) == bet_type)

            portfolio.update(stake, odds, won)

        except Exception:
            continue

    return {
        "final_bankroll": portfolio.bankroll,
        "roi": portfolio.roi(),
        "history": portfolio.history
    }
