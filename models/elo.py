class EloSystem:
    def __init__(self, k=20):
        self.k = k
        self.ratings = {}

    def get(self, team):
        return self.ratings.get(team, 1500)

    def expected(self, r1, r2):
        return 1 / (1 + 10 ** ((r2 - r1) / 400))

    def update(self, team_a, team_b, result):
        # result: 1 = A win, 0.5 = draw, 0 = B win

        ra = self.get(team_a)
        rb = self.get(team_b)

        ea = self.expected(ra, rb)
        eb = 1 - ea

        self.ratings[team_a] = ra + self.k * (result - ea)
        self.ratings[team_b] = rb + self.k * ((1 - result) - eb)
