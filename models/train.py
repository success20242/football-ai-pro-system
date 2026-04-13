import xgboost as xgb
import joblib
import asyncio

from data.build_dataset import build_dataset

print("🚀 Building REAL dataset from APIs...")


async def main():

    df = await build_dataset("PL")

    if len(df) < 50:
        print("⚠️ Not enough real data yet. Need more fixtures/history.")
        return

    X = df[[
        "home_form",
        "away_form",
        "market_edge"
    ]]

    y = df["result"]

    print("🤖 Training institutional model...")

    model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=400,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8
    )

    model.fit(X, y)

    joblib.dump(model, "models/model.pkl")

    print("✅ REAL QUANT MODEL TRAINED & SAVED")


if __name__ == "__main__":
    asyncio.run(main())
