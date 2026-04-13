import xgboost as xgb
import joblib
from features.engineer import build_features

def train(df):

    df = build_features(df)

    X = df[[
        "home_form",
        "away_form",
        "market_edge"
    ]]

    y = df["result"]

    model = xgb.XGBClassifier(
        max_depth=5,
        n_estimators=300,
        subsample=0.8,
        colsample_bytree=0.8
    )

    model.fit(X, y)

    joblib.dump(model, "models/model.pkl")
