import json
import glob
import os
from datetime import datetime
import requests

# === Settings ===
SNAPSHOT_DIR = "snapshots"
THRESHOLD_PCT = 15  # Steamer threshold

# === Load a snapshot file ===
def load_snapshot(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

# === Compare snapshots and detect "steamers" ===
def detect_steamers(snapshot_early, snapshot_late, threshold_pct=THRESHOLD_PCT):
    steam_alerts = []

    for race_url, horses in snapshot_early.items():
        if race_url not in snapshot_late:
            continue

        for horse, start_odds in horses.items():
            end_odds = snapshot_late[race_url].get(horse)
            if not end_odds:
                continue

            drop_pct = (start_odds - end_odds) / start_odds
            if drop_pct >= threshold_pct / 100:
                steam_alerts.append({
                    "race": race_url,
                    "horse": horse,
                    "start_odds": start_odds,
                    "end_odds": end_odds,
                    "drop_pct": round(drop_pct * 100, 2)
                })

    return steam_alerts

# === Get the latest snapshot for a label (e.g., 'morning', 'afternoon') ===
def get_latest_snapshot(label):
    files = sorted(glob.glob(f"{SNAPSHOT_DIR}/odds_snapshot_{label}_*.json"))
    return files[-1] if files else None

# === Send message to Telegram ===
def send_telegram_alert(message):
    try:
        bot_token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"❌ Telegram error: {response.status_code} - {response.text}")
        else:
            print("✅ Alert sent to Telegram.")
    except KeyError:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in environment.")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

# === Main execution ===
if __name__ == "__main__":
    morning_file = get_latest_snapshot("morning")
    afternoon_file = get_latest_snapshot("afternoon")

    if not morning_file or not afternoon_file:
        print("⚠️ Missing snapshots.")
        exit()

    print(f"Comparing snapshots:\n - Morning: {morning_file}\n - Afternoon: {afternoon_file}\n")

    early = load_snapshot(morning_file)
    late = load_snapshot(afternoon_file)

    steamers = detect_steamers(early, late)

    print(f"🔍 Found {len(steamers)} steamers:\n")

    for s in steamers:
        msg = f"""⚠️ *Steamer Alert!*
🏇 *{s['horse']}*
💸 {s['start_odds']} ➡️ {s['end_odds']} (-{s['drop_pct']}%)
📍 Race URL: {s['race']}"""
        print(msg)
        send_telegram_alert(msg)