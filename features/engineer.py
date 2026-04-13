import pandas as pd

def build_features(df):

    # If real columns don't exist, skip complex features
    required_cols = ["home_form", "away_form", "market_edge"]

    for col in required_cols:
        if col not in df.columns:
            df[col] = 0

    return df
