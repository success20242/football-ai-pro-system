import xgboost as xgb
import joblib
import asyncio
import pandas as pd

from data.build_dataset import build_dataset


print("🚀 Building REAL institutional dataset...")


# =========================
# TRAINING PIPELINE (INSTITUTIONAL VERSION)
# =========================
async def main():

    df = await build_dataset("PL")

    if len(df) < 100:
        print("⚠️ Not enough real data yet. Need more historical matches.")
        return

    # =========================
    # CLEAN DATA (IMPORTANT)
    # =========================
    df = df.dropna()

    features = [
        "home_form",
        "away_form",
        "market_edge"
    ]

    X = df[features]
    y = df["result"]

    print("🤖 Training institutional model...")

    model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=500,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss"
    )

    # =========================
    # TIME-AWARE SPLIT (CRITICAL FIX)
    # =========================
    split = int(len(df) * 0.8)

    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    model.fit(X_train, y_train)

    # =========================
    # BASIC VALIDATION
    # =========================
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    print(f"📊 Train Accuracy: {train_score:.3f}")
    print(f"📊 Test Accuracy: {test_score:.3f}")

    # =========================
    # SAVE MODEL
    # =========================
    joblib.dump(model, "models/model.pkl")

    print("✅ INSTITUTIONAL MODEL TRAINED & SAVED")


if __name__ == "__main__":
    asyncio.run(main())
