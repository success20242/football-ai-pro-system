import pandas as pd
from engine.portfolio import Portfolio
from models.predict import predict


def run_backtest(df):
    """
    df must contain:
    - home_form
    - away_form
    - market_edge
    - result (0/1/2)
    - odds_home / odds_away (optional)
    """

    portfolio = Portfolio(bankroll=1000)

    for _, row in df.iterrows():

        features = [
            row["home_form"],
            row["away_form"],
            row["market_edge"]
        ]

        probs = predict(features)

        # pick best side
        home_prob = probs["home_win"]
        away_prob = probs["away_win"]

        if home_prob > away_prob:
            prob = home_prob
            odds = row.get("odds_home", 2.0)
            bet = "HOME"
        else:
            prob = away_prob
            odds = row.get("odds_away", 2.0)
            bet = "AWAY"

        stake = portfolio.kelly_stake(prob, odds)

        if stake <= 0:
            continue

        # result mapping (binary simplification)
        won = (row["result"] == (1 if bet == "HOME" else 0))

        portfolio.update(stake, odds, won)

    return {
        "final_bankroll": portfolio.bankroll,
        "roi": portfolio.roi(),
        "history": portfolio.history
    }
