import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import schedule
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_today_race_urls():
    url = "https://www.oddschecker.com/horse-racing"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, 'html.parser')

    race_urls = set()
    for link in soup.select("a"):
        href = link.get("href", "")
        if "/horse-racing/" in href and "/winner" in href:
            full_url = f"https://www.oddschecker.com{href.split('?')[0]}"
            race_urls.add(full_url)
    return list(race_urls)

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
        return race_data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}

def scrape_all_races(label):
    print(f"Starting scrape: {label}")
    race_urls = get_today_race_urls()
    all_data = {}

    for url in race_urls:
        odds = scrape_race_odds(url)
        if odds:
            all_data[url] = odds

    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"odds_snapshot_{label}_{now}.json"
    with open(filename, 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"Saved snapshot: {filename}")

# Scheduling times
schedule.every().day.at("08:00").do(lambda: scrape_all_races("morning"))
schedule.every().day.at("12:00").do(lambda: scrape_all_races("midday"))
schedule.every().day.at("15:00").do(lambda: scrape_all_races("afternoon"))

# Run loop
if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)
