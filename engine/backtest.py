from engine.portfolio import Portfolio
from models.predict import predict


def normalize_probs(probs):
    total = probs["home_win"] + probs["draw"] + probs["away_win"]
    if total == 0:
        return probs

    return {k: v / total for k, v in probs.items()}


def expected_value(prob, odds):
    return (prob * odds) - 1


def run_backtest(matches: list):

    portfolio = Portfolio(bankroll=1000)

    for match in matches:

        try:
            features = [
                match.get("home_form", 0),
                match.get("away_form", 0),
                match.get("market_edge", 0)
            ]

            probs = normalize_probs(predict(features))

            bets = [
                ("HOME", probs["home_win"], match.get("homeOdds", 2.0)),
                ("DRAW", probs["draw"], match.get("drawOdds", 3.2)),
                ("AWAY", probs["away_win"], match.get("awayOdds", 2.0)),
            ]

            scored = [(b, expected_value(p, o), p, o) for b, p, o in bets]
            best = max(scored, key=lambda x: x[1])

            bet_type, ev, prob, odds = best

            stake = min(portfolio.kelly_stake(prob, odds), portfolio.bankroll * 0.05)

            if stake <= 0 or ev <= 0:
                continue

            result_map = {0: "HOME", 1: "DRAW", 2: "AWAY"}
            actual = result_map.get(match.get("result"))

            won = actual == bet_type

            portfolio.update(stake, odds, won)

        except Exception:
            continue

    return {
        "final_bankroll": portfolio.bankroll,
        "roi": portfolio.roi(),
        "history": portfolio.history
    }
