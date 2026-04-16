import math


class EloSystem:
    def __init__(self, k=20, base=1500, home_advantage=50, decay=0.9995):
        self.k = k
        self.base = base
        self.home_advantage = home_advantage
        self.decay = decay
        self.ratings = {}
        self.history = []

    # =========================
    # GET RATING
    # =========================
    def get(self, team):
        return self.ratings.get(team, self.base)

    # =========================
    # EXPECTED SCORE
    # =========================
    def expected(self, r1, r2):
        return 1 / (1 + 10 ** ((r2 - r1) / 400))

    # =========================
    # APPLY DECAY (TIME DRIFT FIX)
    # =========================
    def apply_decay(self):
        for team in self.ratings:
            self.ratings[team] = self.base + (self.ratings[team] - self.base) * self.decay

    # =========================
    # UPDATE ELO
    # =========================
    def update(self, team_a, team_b, result, goal_a=0, goal_b=0):

        ra = self.get(team_a)
        rb = self.get(team_b)

        # apply home advantage
        ra_adj = ra + self.home_advantage

        ea = self.expected(ra_adj, rb)
        eb = 1 - ea

        # =========================
        # GOAL MARGIN SCALING
        # =========================
        goal_diff = abs(goal_a - goal_b)
        margin_multiplier = math.log(goal_diff + 1) if goal_diff > 0 else 1

        k_factor = self.k * margin_multiplier

        # =========================
        # UPDATE RATING
        # =========================
        new_ra = ra + k_factor * (result - ea)
        new_rb = rb + k_factor * ((1 - result) - eb)

        self.ratings[team_a] = new_ra
        self.ratings[team_b] = new_rb

        # store history for debugging/training alignment
        self.history.append({
            "team_a": team_a,
            "team_b": team_b,
            "ra": ra,
            "rb": rb,
            "ea": ea,
            "result": result,
            "goal_a": goal_a,
            "goal_b": goal_b,
            "new_ra": new_ra,
            "new_rb": new_rb
        })

    # =========================
    # GET FEATURE VALUE
    # =========================
    def diff(self, team_a, team_b):
        return self.get(team_a) - self.get(team_b)

    # =========================
    # NORMALIZED ELO FEATURE
    # =========================
    def normalized_diff(self, team_a, team_b):
        diff = self.diff(team_a, team_b)
        return math.tanh(diff / 400)
