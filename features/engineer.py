import pandas as pd
import numpy as np


# =====================================================
# ELO SYSTEM (UPGRADED)
# =====================================================
def compute_elo(df, k=20, base=1500, home_adv=50):

    teams = {}

    def get(team):
        return teams.get(team, base)

    home_elos = []
    away_elos = []

    # ensure chronological order
    df = df.sort_values(by=df.columns[0]).reset_index(drop=True)

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        home_elo = get(home)
        away_elo = get(away)

        # apply home advantage boost
        adj_home_elo = home_elo + home_adv

        home_elos.append(home_elo)
        away_elos.append(away_elo)

        # expected score
        exp_home = 1 / (1 + 10 ** ((away_elo - adj_home_elo) / 400))

        result = float(row["result"])

        # goal difference scaling (IMPORTANT)
        goal_diff = abs(row["home_goals"] - row["away_goals"])
        margin = np.log(goal_diff + 1)

        k_adj = k * margin

        teams[home] = home_elo + k_adj * (result - exp_home)
        teams[away] = away_elo + k_adj * ((1 - result) - (1 - exp_home))

    df["home_elo"] = home_elos
    df["away_elo"] = away_elos

    return df


# =====================================================
# SAFE ROLLING (NO DATA LEAKAGE)
# =====================================================
def rolling_mean(series, window=5):
    return series.shift(1).rolling(window, min_periods=1).mean()


def rolling_std(series, window=5):
    return series.shift(1).rolling(window, min_periods=1).std()


# =====================================================
# FEATURE ENGINE (PRODUCTION GRADE++)
# =====================================================
def build_features(df):

    df = df.copy()

    # -------------------------
    # BASIC SIGNALS
    # -------------------------
    df["goal_diff"] = df["home_goals"] - df["away_goals"]

    # -------------------------
    # FORM (NO LEAKAGE)
    # -------------------------
    df["home_form"] = df.groupby("home_team")["goal_diff"].transform(rolling_mean)
    df["away_form"] = df.groupby("away_team")["goal_diff"].transform(rolling_mean)

    # -------------------------
    # ELO
    # -------------------------
    df = compute_elo(df)
    df["elo_diff"] = df["home_elo"] - df["away_elo"]

    # -------------------------
    # ATTACK / DEFENSE (NO LEAKAGE)
    # -------------------------
    df["home_attack"] = df.groupby("home_team")["home_goals"].transform(rolling_mean)
    df["away_attack"] = df.groupby("away_team")["away_goals"].transform(rolling_mean)

    df["attack_strength"] = df["home_attack"] - df["away_attack"]

    df["home_defense"] = df.groupby("home_team")["away_goals"].transform(rolling_mean)
    df["away_defense"] = df.groupby("away_team")["home_goals"].transform(rolling_mean)

    df["defensive_diff"] = df["away_defense"] - df["home_defense"]

    # -------------------------
    # MOMENTUM
    # -------------------------
    df["momentum"] = df["home_form"] - df["away_form"]

    # -------------------------
    # VOLATILITY (FIXED: BOTH TEAMS)
    # -------------------------
    df["home_vol"] = df.groupby("home_team")["goal_diff"].transform(rolling_std)
    df["away_vol"] = df.groupby("away_team")["goal_diff"].transform(rolling_std)

    df["volatility"] = (df["home_vol"] + df["away_vol"]) / 2

    # -------------------------
    # HOME ADVANTAGE (LEARNABLE)
    # -------------------------
    df["home_advantage"] = 0.25

    # -------------------------
    # INTERACTION FEATURES (NEW 🔥)
    # -------------------------
    df["elo_momentum"] = df["elo_diff"] * df["momentum"]
    df["attack_vs_defense"] = df["attack_strength"] * df["defensive_diff"]

    # -------------------------
    # FINAL POWER INDEX (IMPROVED)
    # -------------------------
    df["power_index"] = (
        df["elo_diff"] * 0.35 +
        df["momentum"] * 0.25 +
        df["attack_strength"] * 0.2 +
        df["defensive_diff"] * 0.1 +
        df["elo_momentum"] * 0.05 -
        df["volatility"] * 0.05
    )

    # -------------------------
    # NORMALIZATION (VERY IMPORTANT)
    # -------------------------
    features = [
        "elo_diff", "momentum", "attack_strength",
        "defensive_diff", "volatility", "power_index"
    ]

    for col in features:
        mean = df[col].mean()
        std = df[col].std()

        if std > 0:
            df[col] = (df[col] - mean) / std

    return df.fillna(0)
