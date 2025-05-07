import os
import json
from datetime import datetime, timezone
import betfairlightweight
from betfairlightweight import filters

# --- Load credentials from environment ---
USERNAME = os.getenv("BETFAIR_USERNAME")
PASSWORD = os.getenv("BETFAIR_PASSWORD")
APP_KEY = os.getenv("BETFAIR_APP_KEY")

# --- Ensure snapshots directory exists ---
os.makedirs("snapshots", exist_ok=True)

# --- Connect to Betfair Exchange ---
trading = betfairlightweight.APIClient(
    username=USERNAME,
    password=PASSWORD,
    app_key=APP_KEY,
    lightweight=True
)

trading.login()

def get_horse_race_odds():
    # Filter for today's UK horse WIN markets
    market_filter = filters.market_filter(
        event_type_ids=["7"],  # Horse Racing
        market_countries=["GB"],
        market_type_codes=["WIN"],
        market_start_time={
            "from": datetime.now(timezone.utc).isoformat(),
            "to": datetime.now(timezone.utc).replace(hour=23, minute=59).isoformat()
        }
    )

    market_catalogues = trading.betting.list_market_catalogue(
        filter=market_filter,
        market_projection=["RUNNER_METADATA"],
        max_results=20,
        sort="FIRST_TO_START"
    )

    all_data = {}

    for market in market_catalogues:
        market_id = market.market_id
        market_name = market.market_name
        start_time = market.market_start_time.strftime("%Y-%m-%d %H:%M")

        # Fetch live odds (market book)
        market_books = trading.betting.list_market_book(
            market_ids=[market_id],
            price_projection=filters.price_projection(price_data=["EX_BEST_OFFERS"])
        )

        if not market_books:
            continue

        odds = {}
        for runner in market_books[0].runners:
            selection_id = runner.selection_id
            price = None
            if runner.ex.available_to_back:
                price = round(runner.ex.available_to_back[0].price, 2)

            # Get runner name from catalogue
            runner_name = next(
                (r.runner_name for r in market.runners if r.selection_id == selection_id),
                "Unknown"
            )

            if price:
                odds[runner_name] = price

        all_data[f"{start_time} - {market_name}"] = odds

    return all_data

def save_snapshot(data, label="betfair"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"snapshots/odds_snapshot_{label}_{timestamp}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Snapshot saved: {filename}")

def main():
    print(f"\n🚀 Fetching Betfair horse racing odds - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    odds = get_horse_race_odds()
    if odds:
        save_snapshot(odds, label="betfair")
    else:
        print("⚠️ No odds received from Betfair.")

if __name__ == "__main__":
    main()