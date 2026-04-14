import asyncio
import joblib
import numpy as np
import xgboost as xgb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, log_loss

from features.build_dataset import build_dataset


# =========================
# CONFIG
# =========================
FEATURES = [
    "home_form",
    "away_form",
    "market_edge"
]


# =========================
# TRAINING PIPELINE
# =========================
async def main():

    print("🚀 Building REAL dataset...")

    df = await build_dataset("PL", limit=500)

    if len(df) < 100:
        print("⚠️ Not enough real data yet.")
        return

    X = df[FEATURES].values
    y = df["result"].values

    print(f"📊 Dataset size: {len(df)}")

    # =========================
    # WALK-FORWARD VALIDATION
    # =========================
    tscv = TimeSeriesSplit(n_splits=5)

    scores = []
    logloss_scores = []

    print("🧠 Running walk-forward validation...")

    for train_idx, test_idx in tscv.split(X):

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = xgb.XGBClassifier(
            max_depth=6,
            n_estimators=400,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="mlogloss"
        )

        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)

        acc = accuracy_score(y_test, preds)
        loss = log_loss(y_test, probs)

        scores.append(acc)
        logloss_scores.append(loss)

        print(f"Fold → Acc: {acc:.3f} | LogLoss: {loss:.3f}")

    print("\n📊 FINAL VALIDATION RESULTS")
    print(f"Accuracy: {np.mean(scores):.3f}")
    print(f"LogLoss: {np.mean(logloss_scores):.3f}")

    # =========================
    # FINAL MODEL TRAINING
    # =========================
    print("\n🏁 Training FINAL model...")

    final_model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=500,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss"
    )

    final_model.fit(X, y)

    # =========================
    # PROBABILITY CALIBRATION
    # =========================
    print("🎯 Calibrating probabilities...")

    calibrated_model = CalibratedClassifierCV(
        final_model,
        method="isotonic",
        cv=3
    )

    calibrated_model.fit(X, y)

    # =========================
    # SAVE MODEL
    # =========================
    joblib.dump(calibrated_model, "models/model.pkl")

    print("✅ MODEL TRAINED + CALIBRATED + SAVED")


if __name__ == "__main__":
    asyncio.run(main())
