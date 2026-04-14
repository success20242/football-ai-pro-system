class Portfolio:
    def __init__(self, bankroll=1000):
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.history = []

        # 🧠 risk controls
        self.max_fraction = 0.25   # max Kelly fraction
        self.max_bet = 0.05        # max 5% bankroll per bet

    def kelly_stake(self, prob, odds, fraction=0.25):
        """
        Fractional Kelly with safety caps
        """

        if odds <= 1 or prob <= 0:
            return 0

        b = odds - 1
        q = 1 - prob

        kelly = (b * prob - q) / b

        # ❌ no negative bets
        if kelly <= 0:
            return 0

        # 🧠 fractional Kelly (risk reduction)
        kelly *= fraction

        # 🛑 clamp to safety limits
        kelly = min(kelly, self.max_bet)

        stake = self.bankroll * kelly

        # final safety check
        return max(0, stake)

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

    def drawdown(self):
        peak = self.initial_bankroll
        max_dd = 0

        for value in self.history:
            peak = max(peak, value)
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)

        return max_dd
