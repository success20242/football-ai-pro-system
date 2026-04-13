import pandas as pd
import numpy as np


# =========================
# ELO CALCULATION SYSTEM
# =========================
def compute_elo(df, k=20, base=1500):
    teams = {}

    def get(team):
        return teams.get(team, base)

    elos_home = []
    elos_away = []

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        home_elo = get(home)
        away_elo = get(away)

        elos_home.append(home_elo)
        elos_away.append(away_elo)

        # expected score
        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))

        result = row["result"]

        # update
        teams[home] = home_elo + k * (result - exp_home)
        teams[away] = away_elo + k * ((1 - result) - (1 - exp_home))

    df["home_elo"] = elos_home
    df["away_elo"] = elos_away

    return df


# =========================
# FEATURE ENGINE
# =========================
def build_features(df):

    # -------------------------
    # BASIC GOAL STATS
    # -------------------------
    df["goal_diff"] = df["home_goals"] - df["away_goals"]

    df["home_form"] = df.groupby("home_team")["goal_diff"].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df["away_form"] = df.groupby("away_team")["goal_diff"].transform(lambda x: x.rolling(5, min_periods=1).mean())

    # -------------------------
    # HOME ADVANTAGE MODEL
    # -------------------------
    df["home_advantage"] = 0.3

    # -------------------------
    # MARKET EDGE
    # -------------------------
    if "model_prob" in df.columns and "market_prob" in df.columns:
        df["market_edge"] = df["model_prob"] - df["market_prob"]
    else:
        df["market_edge"] = 0

    # -------------------------
    # ADD ELO SYSTEM
    # -------------------------
    df = compute_elo(df)

    df["elo_diff"] = df["home_elo"] - df["away_elo"]

    # -------------------------
    # FINAL CLEAN FEATURES
    # -------------------------
    return df.dropna()
