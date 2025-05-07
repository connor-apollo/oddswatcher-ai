import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
from datetime import datetime
import schedule

# Set headers to mimic browser
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Ensure snapshots folder exists
os.makedirs("snapshots", exist_ok=True)

# Get all today's UK race URLs from Oddschecker
def get_today_race_urls():
    url = "https://www.oddschecker.com/horse-racing"
    try:
        resp = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        race_urls = set()
        for link in soup.select("a"):
            href = link.get("href", "")
            if "/horse-racing/" in href and "/winner" in href:
                full_url = f"https://www.oddschecker.com{href.split('?')[0]}"
                race_urls.add(full_url)

        print(f"Found {len(race_urls)} race URLs.")
        return list(race_urls)

    except Exception as e:
        print(f"Error getting race URLs: {e}")
        return []

# Scrape odds for one race
def scrape_race_odds(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        race_data = {}
        for row in soup.select('.racecard-row'):
            horse_tag = row.select_one('.horse-name')
            odds_tag = row.select_one('.best-price')

            if horse_tag and odds_tag:
                name = horse_tag.text.strip()
                odds_text = odds_tag.text.strip()
                match = re.match(r"(\d+)/(\d+)", odds_text)

                if match:
                    num, denom = map(int, match.groups())
                    decimal_odds = round(1 + num / denom, 2)
                elif odds_text.lower() == "evens":
                    decimal_odds = 2.0
                else:
                    continue

                race_data[name] = decimal_odds

        print(f"Scraped {len(race_data)} horses from {url}")
        return race_data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

# Scrape all races and save a snapshot
def scrape_all_races(label):
    print(f"\n🚀 Starting scrape: {label} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    race_urls = get_today_race_urls()
    all_data = {}

    for url in race_urls:
        odds = scrape_race_odds(url)
        if odds:
            all_data[url] = odds
        time.sleep(1.5)  # Delay to avoid being blocked

    if all_data:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"snapshots/odds_snapshot_{label}_{now}.json"
        with open(filename, 'w') as f:
            json.dump(all_data, f, indent=2)
        print(f"✅ Saved snapshot: {filename}")
    else:
        print("⚠️ No race data collected.")

# Schedule daily snapshots
schedule.every().day.at("08:00").do(lambda: scrape_all_races("morning"))
schedule.every().day.at("12:00").do(lambda: scrape_all_races("midday"))
schedule.every().day.at("15:00").do(lambda: scrape_all_races("afternoon"))

# Keep script running
if __name__ == "__main__":
    print("🔁 Scheduler started. Waiting for next job...")
    while True:
        schedule.run_pending()
        time.sleep(60)
