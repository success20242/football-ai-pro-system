import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ODDS_API_KEY")

BASE_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"


# =========================
# SAFE FETCH (WITH DEBUG)
# =========================
async def fetch(params: dict):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)

            if r.status_code == 429:
                print("⚠️ ODDS API RATE LIMIT HIT")
                return []

            if r.status_code != 200:
                print(f"❌ ODDS API ERROR {r.status_code}")
                return []

            data = r.json()

            if isinstance(data, list):
                return data

            return data.get("data", []) if isinstance(data, dict) else []

    except Exception as e:
        print(f"❌ ODDS FETCH ERROR → {e}")
        return []


# =========================
# IMPLIED PROBABILITY
# =========================
def implied_prob(odds: float):
    try:
        return round(1 / float(odds), 4) if odds else 0.0
    except:
        return 0.0


# =========================
# NORMALIZE GAME (PRO VERSION)
# =========================
def normalize_game(game: dict):
    try:
        if not isinstance(game, dict):
            return None

        game_id = game.get("id")
        home_team = game.get("home_team")
        away_team = game.get("away_team")

        bookmakers = game.get("bookmakers", [])
        if not bookmakers:
            return None

        # ✅ pick first bookmaker with valid markets
        market = None
        for bm in bookmakers:
            markets = bm.get("markets", [])
            if markets:
                market = markets[0]
                break

        if not market:
            return None

        outcomes = market.get("outcomes", [])
        if not outcomes:
            return None

        odds = {"home": None, "away": None, "draw": None}

        # ✅ CORRECT TEAM MATCHING
        for o in outcomes:
            name = (o.get("name") or "").lower()
            price = float(o.get("price") or 2.0)

            if "draw" in name:
                odds["draw"] = price

            elif home_team and name == home_team.lower():
                odds["home"] = price

            elif away_team and name == away_team.lower():
                odds["away"] = price

        # ⚠️ fallback if names don't match exactly
        for o in outcomes:
            price = float(o.get("price") or 2.0)

            if odds["home"] is None:
                odds["home"] = price
            elif odds["away"] is None:
                odds["away"] = price

        if odds["home"] is None or odds["away"] is None:
            return None

        draw = odds["draw"] if odds["draw"] else 3.2

        # ✅ probabilities (VERY IMPORTANT)
        probs = {
            "home_prob": implied_prob(odds["home"]),
            "draw_prob": implied_prob(draw),
            "away_prob": implied_prob(odds["away"])
        }

        return {
            "id": game_id,  # ✅ unified key
            "home": odds["home"],
            "draw": draw,
            "away": odds["away"],
            "probs": probs
        }

    except Exception as e:
        print(f"❌ NORMALIZE ERROR → {e}")
        return None


# =========================
# MAIN PIPELINE
# =========================
async def get_odds():

    if not API_KEY:
        print("⚠️ NO ODDS API KEY")
        return []

    params = {
        "apiKey": API_KEY,
        "regions": "eu",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    raw = await fetch(params)

    if not isinstance(raw, list):
        return []

    normalized = []

    for g in raw:
        parsed = normalize_game(g)
        if parsed:
            normalized.append(parsed)

    print(f"✅ ODDS LOADED: {len(normalized)} matches")

    return normalized
