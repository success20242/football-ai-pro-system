import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# =========================
# API KEYS
# =========================
FD_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
RAPID_API_KEY = os.getenv("FOOTBALL_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

FD_BASE = "https://api.football-data.org/v4"
RAPID_BASE = "https://api-football-v1.p.rapidapi.com/v3"
ODDS_BASE = "https://api.the-odds-api.com/v4"


# =========================
# HEADERS
# =========================
FD_HEADERS = {"X-Auth-Token": FD_API_KEY} if FD_API_KEY else {}

RAPID_HEADERS = {
    "x-rapidapi-key": RAPID_API_KEY,
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
} if RAPID_API_KEY else {}


# =========================
# SAFE FETCH (SMART + DEBUG)
# =========================
async def fetch(url: str, headers=None, params=None):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)

            if r.status_code == 429:
                print(f"⚠️ RATE LIMIT HIT → {url}")
                return None

            if r.status_code != 200:
                print(f"❌ API ERROR {r.status_code} → {url}")
                return None

            return r.json()

    except Exception as e:
        print(f"❌ FETCH ERROR → {e}")
        return None


# =========================
# SAFE HELPERS
# =========================
def safe_dict(data):
    return data if isinstance(data, dict) else {}


def safe_list(data):
    return data if isinstance(data, list) else []


# =========================
# NORMALIZERS (CRITICAL FIX)
# =========================
def normalize_fd_match(m):
    try:
        return {
            "id": m.get("id"),
            "league": m.get("competition", {}).get("name"),
            "timestamp": m.get("utcDate"),
            "status": m.get("status"),

            "homeTeam": {
                "id": m.get("homeTeam", {}).get("id"),
                "name": m.get("homeTeam", {}).get("name")
            },
            "awayTeam": {
                "id": m.get("awayTeam", {}).get("id"),
                "name": m.get("awayTeam", {}).get("name")
            }
        }
    except:
        return None


def normalize_rapid_match(m):
    try:
        return {
            "id": m.get("fixture", {}).get("id"),
            "league": m.get("league", {}).get("name"),
            "timestamp": m.get("fixture", {}).get("date"),
            "status": m.get("fixture", {}).get("status", {}).get("short"),

            "homeTeam": {
                "id": m.get("teams", {}).get("home", {}).get("id"),
                "name": m.get("teams", {}).get("home", {}).get("name")
            },
            "awayTeam": {
                "id": m.get("teams", {}).get("away", {}).get("id"),
                "name": m.get("teams", {}).get("away", {}).get("name")
            }
        }
    except:
        return None


# =========================
# LIVE MATCHES (RAPID → FD FALLBACK)
# =========================
async def get_live_matches():

    # ✅ PRIMARY: RAPID API
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"live": "all"}
        )

        matches = safe_list(data.get("response") if data else [])
        cleaned = [normalize_rapid_match(m) for m in matches]
        cleaned = [m for m in cleaned if m]

        if cleaned:
            return {"matches": cleaned}

    # ⚠️ FALLBACK: FOOTBALL DATA
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/matches",
            headers=FD_HEADERS,
            params={"status": "LIVE"}
        )

        matches = safe_list(data.get("matches") if data else [])
        cleaned = [normalize_fd_match(m) for m in matches]

        return {"matches": [m for m in cleaned if m]}

    return {"matches": []}


# =========================
# UPCOMING MATCHES
# =========================
async def get_upcoming_matches():

    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/fixtures",
            headers=RAPID_HEADERS,
            params={"next": 10}
        )

        matches = safe_list(data.get("response") if data else [])
        cleaned = [normalize_rapid_match(m) for m in matches]

        return {"matches": [m for m in cleaned if m]}

    if FD_API_KEY:
        data = await fetch(f"{FD_BASE}/matches", headers=FD_HEADERS)

        matches = safe_list(data.get("matches") if data else [])
        cleaned = [normalize_fd_match(m) for m in matches]

        return {"matches": [m for m in cleaned if m]}

    return {"matches": []}


# =========================
# TEAM STATS (SMART HYBRID)
# =========================
async def get_team_stats(team_id: int):

    # ✅ TRY RAPID FIRST (better data)
    if RAPID_API_KEY:
        data = await fetch(
            f"{RAPID_BASE}/teams",
            headers=RAPID_HEADERS,
            params={"id": team_id}
        )

        response = safe_list(data.get("response") if data else [])
        if response:
            return response[0]

    # ⚠️ FALLBACK
    if FD_API_KEY:
        data = await fetch(
            f"{FD_BASE}/teams/{team_id}",
            headers=FD_HEADERS
        )
        return safe_dict(data)

    return {}


# =========================
# ODDS (NORMALIZED CLEAN)
# =========================
async def get_match_odds(sport="soccer_epl"):

    if not ODDS_API_KEY:
        return []

    data = await fetch(
        f"{ODDS_BASE}/sports/{sport}/odds",
        params={
            "apiKey": ODDS_API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
    )

    raw = safe_list(data)

    normalized = []

    for game in raw:
        try:
            bookmakers = game.get("bookmakers", [])
            if not bookmakers:
                continue

            outcomes = bookmakers[0].get("markets", [{}])[0].get("outcomes", [])

            odds = {"home": 2.0, "draw": 3.2, "away": 2.0}

            for o in outcomes:
                name = o.get("name", "").lower()
                price = float(o.get("price", 2.0))

                if "draw" in name:
                    odds["draw"] = price
                elif odds["home"] == 2.0:
                    odds["home"] = price
                else:
                    odds["away"] = price

            normalized.append({
                "id": game.get("id"),
                "home": odds["home"],
                "draw": odds["draw"],
                "away": odds["away"]
            })

        except:
            continue

    return normalized
