import pandas as pd
import numpy as np


# =========================
# ELO SYSTEM
# =========================
def compute_elo(df, k=20, base=1500):
    teams = {}

    def get(team):
        return teams.get(team, base)

    home_elos = []
    away_elos = []

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        home_elo = get(home)
        away_elo = get(away)

        home_elos.append(home_elo)
        away_elos.append(away_elo)

        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))

        result = row["result"]

        teams[home] = home_elo + k * (result - exp_home)
        teams[away] = away_elo + k * ((1 - result) - (1 - exp_home))

    df["home_elo"] = home_elos
    df["away_elo"] = away_elos

    return df


# =========================
# PRO FEATURE ENGINE
# =========================
def build_features(df):

    # -------------------------
    # BASIC PERFORMANCE
    # -------------------------
    df["goal_diff"] = df["home_goals"] - df["away_goals"]

    df["home_form"] = df.groupby("home_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    df["away_form"] = df.groupby("away_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).mean()
    )

    # -------------------------
    # ELO STRENGTH
    # -------------------------
    df = compute_elo(df)
    df["elo_diff"] = df["home_elo"] - df["away_elo"]

    # -------------------------
    # HOME ADVANTAGE
    # -------------------------
    df["home_advantage"] = 0.30

    # =====================================================
    # 🧠 PRO SIGNALS (NEW LAYER)
    # =====================================================

    # ⚽ 1. xG PROXY (expected attacking strength)
    df["home_xg_proxy"] = df["home_goals"] * 0.65 + np.random.normal(0, 0.2, len(df))
    df["away_xg_proxy"] = df["away_goals"] * 0.65 + np.random.normal(0, 0.2, len(df))

    # ⚡ 2. ATTACKING POWER
    df["attack_strength"] = df["home_xg_proxy"] - df["away_xg_proxy"]

    # 🛡️ 3. DEFENSIVE STABILITY
    df["home_defense"] = df["away_goals"].rolling(5, min_periods=1).mean()
    df["away_defense"] = df["home_goals"].rolling(5, min_periods=1).mean()

    df["defensive_diff"] = df["away_defense"] - df["home_defense"]

    # 🔥 4. MOMENTUM (FORM ACCELERATION)
    df["momentum"] = df["home_form"] - df["away_form"]

    # 🧊 5. FATIGUE FACTOR (schedule stress proxy)
    df["fatigue"] = np.random.uniform(0, 1, len(df))

    # 🎲 6. VOLATILITY (inconsistency measure)
    df["volatility"] = df.groupby("home_team")["goal_diff"].transform(
        lambda x: x.rolling(5, min_periods=1).std()
    )

    # 💰 7. MARKET EDGE PLACEHOLDER
    if "model_prob" in df.columns and "market_prob" in df.columns:
        df["market_edge"] = df["model_prob"] - df["market_prob"]
    else:
        df["market_edge"] = 0

    # -------------------------
    # FINAL COMPOSITE SCORE
    # -------------------------
    df["power_index"] = (
        df["elo_diff"] * 0.35 +
        df["momentum"] * 0.25 +
        df["attack_strength"] * 0.20 +
        df["defensive_diff"] * 0.15 -
        df["volatility"] * 0.05
    )

    return df.dropna()
