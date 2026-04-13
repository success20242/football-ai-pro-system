import time
from models.predict import predict
from engine.value_bets import is_value

def run_live(data_stream):

    while True:
        data = next(data_stream)

        pred = predict(data["features"])

        if is_value(pred["home"], data["odds"]):
            print("🔥 LIVE VALUE BET")

        time.sleep(5)
