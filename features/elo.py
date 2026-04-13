def expected(r1, r2):
    return 1 / (1 + 10 ** ((r2 - r1) / 400))

def update(rating, expected, actual, k=25):
    return rating + k * (actual - expected)
