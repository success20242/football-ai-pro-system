import math


# =========================
# EXPECTED SCORE
# =========================
def expected(r1, r2):
    return 1 / (1 + 10 ** ((r2 - r1) / 400))


# =========================
# CORE UPDATE (IMPROVED)
# =========================
def update(rating, expected_score, actual, k=25, goal_diff=1):
    """
    Elo update with goal margin scaling
    """

    margin_multiplier = math.log(goal_diff + 1)

    return rating + k * margin_multiplier * (actual - expected_score)


# =========================
# TEAM ELO SYSTEM (PRODUCTION CLASS)
# =========================
class EloSystem:

    def __init__(self, base=1500, home_advantage=50):
        self.base = base
        self.home_advantage = home_advantage
        self.ratings = {}

    # -------------------------
    # GET RATING
    # -------------------------
    def get(self, team):
        return self.ratings.get(team, self.base)

    # -------------------------
    # EXPECTED SCORE (HOME BOOST INCLUDED)
    # -------------------------
    def expected(self, home_rating, away_rating):
        return expected(home_rating + self.home_advantage, away_rating)

    # -------------------------
    # UPDATE MATCH
    # result: 1=home win, 0.5=draw, 0=away win
    # -------------------------
    def update_match(self, home, away, result, home_goals=0, away_goals=0):

        r_home = self.get(home)
        r_away = self.get(away)

        exp_home = self.expected(r_home, r_away)
        exp_away = 1 - exp_home

        goal_diff = abs(home_goals - away_goals)
        goal_diff = max(1, goal_diff)

        new_home = update(r_home, exp_home, result, goal_diff=goal_diff)
        new_away = update(r_away, exp_away, 1 - result, goal_diff=goal_diff)

        self.ratings[home] = new_home
        self.ratings[away] = new_away

        return new_home, new_away

    # -------------------------
    # FEATURE EXTRACTION
    # -------------------------
    def diff(self, home, away):
        return self.get(home) - self.get(away)

    # -------------------------
    # NORMALIZED FEATURE (ML SAFE)
    # -------------------------
    def normalized_diff(self, home, away):
        return math.tanh(self.diff(home, away) / 400)
