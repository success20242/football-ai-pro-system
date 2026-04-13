import xgboost as xgb
import joblib
import pandas as pd
from features.engineer import build_features

print("🚀 Loading dataset...")

# TEMP DATA (we will replace with real API data next)
df = pd.DataFrame({
    "home_form": [0.1, 0.5, 0.3, 0.9, 0.2],
    "away_form": [0.2, 0.4, 0.6, 0.1, 0.8],
    "market_edge": [0.05, -0.1, 0.2, 0.0, 0.3],
    "result": [1, 0, 1, 1, 0]
})

print("⚙️ Building features...")
df = build_features(df)

X = df[[
    "home_form",
    "away_form",
    "market_edge"
]]

y = df["result"]

print("🤖 Training model...")

model = xgb.XGBClassifier(
    max_depth=5,
    n_estimators=300,
    subsample=0.8,
    colsample_bytree=0.8
)

model.fit(X, y)

print("💾 Saving model...")

joblib.dump(model, "models/model.pkl")

print("✅ TRAINING COMPLETE")
