import time
from models.predict import predict
from engine.value_bets import is_value


# =========================
# SAFE STREAM WRAPPER
# =========================
def safe_next(stream):
    try:
        return next(stream)
    except StopIteration:
        return None
    except Exception:
        return None


# =========================
# MAIN LIVE ENGINE (FIXED)
# =========================
def run_live(data_stream, delay=3):

    print("🚀 Live engine started...")

    while True:

        try:
            data = safe_next(data_stream)

            if data is None:
                time.sleep(1)
                continue

            # -------------------------
            # VALIDATE INPUT
            # -------------------------
            if not isinstance(data, dict):
                continue

            features = data.get("features", [])
            odds = data.get("odds", {})

            # -------------------------
            # PREDICTION
            # -------------------------
            pred = predict(features)

            if not isinstance(pred, dict):
                continue

            probs = pred.get("probs", {})

            home_p = probs.get("home", 0)
            draw_p = probs.get("draw", 0)
            away_p = probs.get("away", 0)

            # -------------------------
            # VALUE CHECK
            # -------------------------
            if is_value(home_p, odds.get("home")):
                print("🔥 LIVE VALUE BET → HOME")

            if is_value(draw_p, odds.get("draw")):
                print("🔥 LIVE VALUE BET → DRAW")

            if is_value(away_p, odds.get("away")):
                print("🔥 LIVE VALUE BET → AWAY")

            # -------------------------
            # CONTROL LOOP SPEED
            # -------------------------
            time.sleep(delay)

        except KeyboardInterrupt:
            print("🛑 Live engine stopped manually")
            break

        except Exception as e:
            print(f"⚠️ Live engine error: {e}")
            time.sleep(2)
