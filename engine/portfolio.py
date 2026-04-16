class Portfolio:

    def __init__(self, bankroll=1000):
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.history = []

        # =========================
        # RISK CONTROLS
        # =========================
        self.max_fraction = 0.25   # max Kelly fraction
        self.max_bet_pct = 0.05     # max 5% bankroll per bet
        self.min_bankroll = bankroll * 0.2  # survival floor

        # stats tracking
        self.total_bets = 0
        self.wins = 0

    # =========================
    # KELLY STAKE (FIXED)
    # =========================
    def kelly_stake(self, prob, odds, fraction=0.25):

        if odds <= 1 or prob <= 0:
            return 0

        b = odds - 1
        q = 1 - prob

        kelly = (b * prob - q) / b

        if kelly <= 0:
            return 0

        # fractional Kelly
        kelly *= fraction

        # clamp to max fraction of bankroll (IMPORTANT FIX)
        kelly = min(kelly, self.max_bet_pct)

        stake = self.bankroll * kelly

        return max(0, stake)

    # =========================
    # UPDATE BANKROLL
    # =========================
    def update(self, stake, odds, won):

        if stake <= 0:
            return

        self.total_bets += 1

        if won:
            profit = stake * (odds - 1)
            self.bankroll += profit
            self.wins += 1
        else:
            self.bankroll -= stake

        # =========================
        # SAFETY FLOOR (SURVIVAL MODE)
        # =========================
        if self.bankroll < self.min_bankroll:
            self.bankroll = self.min_bankroll

        self.history.append(self.bankroll)

    # =========================
    # ROI
    # =========================
    def roi(self):
        return (self.bankroll - self.initial_bankroll) / self.initial_bankroll

    # =========================
    # DRAW DOWN
    # =========================
    def drawdown(self):
        peak = self.initial_bankroll
        max_dd = 0

        for value in self.history:
            peak = max(peak, value)
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)

        return max_dd

    # =========================
    # WIN RATE
    # =========================
    def win_rate(self):
        if self.total_bets == 0:
            return 0
        return self.wins / self.total_bets

    # =========================
    # RISK HEALTH SCORE
    # =========================
    def health_score(self):
        """
        Simple institutional metric:
        combines ROI, drawdown, and win rate
        """
        roi = self.roi()
        dd = self.drawdown()
        wr = self.win_rate()

        return (roi * 0.5) + (wr * 0.3) - (dd * 0.2)
