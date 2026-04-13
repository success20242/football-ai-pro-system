import xgboost as xgb
import joblib
import pandas as pd
from features.engineer import build_features

print("🚀 Loading dataset...")

# TEMP DATA (3-class football system)
df = pd.DataFrame({
    "home_form": [0.1, 0.5, 0.3, 0.9, 0.2, 0.8],
    "away_form": [0.2, 0.4, 0.6, 0.1, 0.8, 0.3],
    "market_edge": [0.05, -0.1, 0.2, 0.0, 0.3, -0.2],
    # 0 = away win, 1 = draw, 2 = home win
    "result": [2, 0, 1, 2, 0, 2]
})

print("⚙️ Building features...")
df = build_features(df)

X = df[[
    "home_form",
    "away_form",
    "market_edge"
]]

y = df["result"]

print("🤖 Training 3-class model...")

model = xgb.XGBClassifier(
    max_depth=5,
    n_estimators=300,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    num_class=3
)

model.fit(X, y)

print("💾 Saving model...")

joblib.dump(model, "models/model.pkl")

print("✅ TRAINING COMPLETE (3-class football AI ready)")
