import json
import glob
from datetime import datetime

def load_snapshot(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def detect_steamers(snapshot_early, snapshot_late, threshold_pct=15):
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

def get_latest_snapshot(label):
    files = sorted(glob.glob(f"odds_snapshot_{label}_*.json"))
    return files[-1] if files else None

if __name__ == "__main__":
    morning_file = get_latest_snapshot("morning")
    afternoon_file = get_latest_snapshot("afternoon")

    if not morning_file or not afternoon_file:
        print("Missing snapshots.")
        exit()

    early = load_snapshot(morning_file)
    late = load_snapshot(afternoon_file)

    steamers = detect_steamers(early, late)

    print(f"🔍 Found {len(steamers)} steamers:\n")
    for s in steamers:
        print(f"⚡ {s['horse']} ({s['race']}): {s['start_odds']} → {s['end_odds']} (-{s['drop_pct']}%)")
