import pandas as pd

def build_features(df):

    df["goal_diff"] = df["home_goals"] - df["away_goals"]

    df["home_form"] = df.groupby("home_team")["goal_diff"].rolling(5).mean().reset_index(0, drop=True)
    df["away_form"] = df.groupby("away_team")["goal_diff"].rolling(5).mean().reset_index(0, drop=True)

    df["market_edge"] = df["model_prob"] - df["market_prob"]

    return df.dropna()
