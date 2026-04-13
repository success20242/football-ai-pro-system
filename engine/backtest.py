import pandas as pd
from engine.portfolio import Portfolio
from models.predict import predict


def run_backtest(df):
    """
    df must contain:
    - home_form
    - away_form
    - market_edge
    - result (0=home, 1=draw, 2=away)
    - odds_home / odds_draw / odds_away (optional)
    """

    portfolio = Portfolio(bankroll=1000)

    for _, row in df.iterrows():

        features = [
            row["home_form"],
            row["away_form"],
            row["market_edge"]
        ]

        probs = predict(features)

        home_p = probs["home_win"]
        draw_p = probs["draw"]
        away_p = probs["away_win"]

        # 🎯 pick best value bet (EV-based selection)
        bets = [
            ("HOME", home_p, row.get("odds_home", 2.0)),
            ("DRAW", draw_p, row.get("odds_draw", 3.2)),
            ("AWAY", away_p, row.get("odds_away", 2.0)),
        ]

        best_bet = max(bets, key=lambda x: x[1] * x[2])

        bet_type, prob, odds = best_bet

        stake = portfolio.kelly_stake(prob, odds)

        if stake <= 0:
            continue

        # 🧠 result mapping (correct 3-way system)
        result_map = {
            0: "HOME",
            1: "DRAW",
            2: "AWAY"
        }

        won = (result_map[row["result"]] == bet_type)

        portfolio.update(stake, odds, won)

    return {
        "final_bankroll": portfolio.bankroll,
        "roi": portfolio.roi(),
        "history": portfolio.history
    }
