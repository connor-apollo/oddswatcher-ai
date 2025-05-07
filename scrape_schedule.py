import requests
import os
import json
from datetime import datetime

# Make sure this folder exists
os.makedirs("snapshots", exist_ok=True)

# Read your API key from environment variable
API_KEY = os.getenv("ODDS_API_KEY")

# Configuration
SPORT = 'horse_racing_uk'
REGION = 'uk'
MARKET = 'h2h'  # head-to-head market

def get_odds():
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': REGION,
        'markets': MARKET,
        'oddsFormat': 'decimal'
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ API error: {response.status_code} - {response.text}")
        return {}

    data = response.json()
    print(f"✅ Received {len(data)} events.")

    parsed_data = {}
    for event in data:
        race_name = event.get("home_team")
        bookmakers = event.get("bookmakers", [])
        if not bookmakers:
            continue

        outcomes = bookmakers[0]["markets"][0]["outcomes"]
        horse_odds = {outcome["name"]: outcome["price"] for outcome in outcomes}
        parsed_data[race_name] = horse_odds

    return parsed_data

def save_snapshot(data, label="api"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"snapshots/odds_snapshot_{label}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"📁 Snapshot saved to: {filename}")

def main():
    print(f"\n🚀 Fetching odds via The Odds API - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    odds = get_odds()
    if odds:
        save_snapshot(odds, label="manual-test")
    else:
        print("⚠️ No data received from API.")

if __name__ == "__main__":
    main()