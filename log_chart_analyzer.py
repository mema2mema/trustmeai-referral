# log_chart_analyzer.py

import pandas as pd
import matplotlib.pyplot as plt
import json
import requests
import os

# Load Telegram credentials from JSON
with open("telegram_config.json", "r") as f:
    config = json.load(f)
    TELEGRAM_BOT_TOKEN = config["bot_token"]
    TELEGRAM_CHAT_ID = config["chat_id"]

# Constants
LOG_FILE = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"
DRAW_THRESHOLD = 0.25

def send_telegram_photo(photo_path, caption="📊 Trade Summary"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"photo": photo})

def check_ai_warnings(balances, initial_balance):
    warnings = []

    # 1. Profit drop check
    if len(balances) >= 2 and balances[-1] < balances[-2]:
        warnings.append("⚠️ Profit dropped after last trade.")

    # 2. Drawdown check
    peak = max(balances)
    trough = min(balances)
    drawdown = (peak - trough) / peak
    if drawdown > DRAW_THRESHOLD:
        warnings.append(f"⚠️ Drawdown exceeds 25%: {drawdown:.2%}")

    # 3. Unrealistic compound growth
    growth = balances[-1] / initial_balance
    if growth > 10 and len(balances) < 10:
        warnings.append(f"⚠️ Unrealistic growth: {growth:.2f}x in {len(balances)} trades.")

    return warnings

def analyze_log():
    if not os.path.exists(LOG_FILE):
        print("❌ Log file not found:", LOG_FILE)
        return

    df = pd.read_csv(LOG_FILE)
    balances = df["Balance"].tolist()
    initial_balance = balances[0] if balances else 1000

    # Plot the balance chart
    plt.figure()
    plt.plot(balances, marker='o')
    plt.title("Autobot Balance Over Time (From Log)")
    plt.xlabel("Trade #")
    plt.ylabel("Balance")
    plt.grid(True)
    plt.savefig(CHART_FILE)
    plt.close()

    # AI analysis
    warnings = check_ai_warnings(balances, initial_balance)
    caption = "📊 Autobot log analysis complete.\n\n"
    caption += "\n".join(warnings) if warnings else "✅ No warnings. All looks good."

    # Send to Telegram
    send_telegram_photo(CHART_FILE, caption=caption)
    print("✅ Chart sent to Telegram.")

if __name__ == "__main__":
    analyze_log()
