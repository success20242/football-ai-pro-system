import pandas as pd
import numpy as np


# =====================================================
# ELO SYSTEM (CLEAN + DETERMINISTIC)
# =====================================================
def compute_elo(df, k=20, base=1500):

    teams = {}

    def get(team):
        return teams.get(team, base)

    home_elos = []
    away_elos = []

    # IMPORTANT: enforce time order (CRITICAL FIX)
    df = df.sort_values(by=df.columns[0]).reset_index(drop=True)

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        home_elo = get(home)
        away_elo = get(away)

        home_elos.append(home_elo)
        away_elos.append(away_elo)

        # expected score
        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))

        result = float(row["result"])

        teams[home] = home_elo + k * (result - exp_home)
        teams[away] = away_elo + k * ((1 - result) - (1 - exp_home))

    df["home_elo"] = home_elos
    df["away_elo"] = away_elos

    return df


# =====================================================
# FEATURE ENGINE (PRODUCTION GRADE)
# =====================================================
def build_features(df):

    df = df.copy()

    # -------------------------
    # BASIC SIGNALS
    # -------------------------
    df["goal_diff"] = df["home_goals"] - df["away_goals"]

    df["home_form"] = df.groupby("home_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["away_form"] = df.groupby("away_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    # -------------------------
    # ELO
    # -------------------------
    df = compute_elo(df)
    df["elo_diff"] = df["home_elo"] - df["away_elo"]

    # -------------------------
    # FIXED ATTACK / DEFENSE (NO RANDOMNESS)
    # -------------------------
    df["home_attack"] = df.groupby("home_team")["home_goals"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["away_attack"] = df.groupby("away_team")["away_goals"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["attack_strength"] = df["home_attack"] - df["away_attack"]

    df["home_defense"] = df.groupby("home_team")["away_goals"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["away_defense"] = df.groupby("away_team")["home_goals"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["defensive_diff"] = df["away_defense"] - df["home_defense"]

    # -------------------------
    # MOMENTUM
    # -------------------------
    df["momentum"] = df["home_form"] - df["away_form"]

    # -------------------------
    # STABILITY (VOLATILITY)
    # -------------------------
    df["volatility"] = df.groupby("home_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).std()
    ).fillna(0)

    # -------------------------
    # HOME ADVANTAGE (FIXED CONSTANT)
    # -------------------------
    df["home_advantage"] = 0.25

    # -------------------------
    # FINAL QUANT SCORE
    # -------------------------
    df["power_index"] = (
        df["elo_diff"] * 0.4 +
        df["momentum"] * 0.3 +
        df["attack_strength"] * 0.2 +
        df["defensive_diff"] * 0.1 -
        df["volatility"] * 0.05
    )

    return df.fillna(0)
