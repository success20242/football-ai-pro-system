class Portfolio:
    def __init__(self, bankroll=1000):
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.history = []

    def kelly_stake(self, prob, odds, fraction=0.25):
        """
        Kelly Criterion (fractional for safety)
        """

        b = odds - 1
        q = 1 - prob

        kelly = (b * prob - q) / b

        if kelly < 0:
            return 0

        return self.bankroll * kelly * fraction

    def update(self, stake, odds, won):
        if stake <= 0:
            return

        if won:
            profit = stake * (odds - 1)
            self.bankroll += profit
        else:
            self.bankroll -= stake

        self.history.append(self.bankroll)

    def roi(self):
        return (self.bankroll - self.initial_bankroll) / self.initial_bankroll
