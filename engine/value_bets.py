from core.config import Config

def is_value(model_prob, odds):

    market_prob = 1 / odds
    return model_prob - market_prob > Config.VALUE_THRESHOLD
