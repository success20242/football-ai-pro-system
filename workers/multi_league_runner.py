from data.ingestion import fetch_matches, LEAGUES

def run_all():
    all_data = []

    for league in LEAGUES:
        data = fetch_matches(league)
        all_data.append(data)

    return all_data
