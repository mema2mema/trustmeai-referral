# autobot_runner.py

import json
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
import requests

CONFIG_FILE = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"
LOG_FILE = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"
TELEGRAM_CONFIG = "telegram_config.json"

def send_telegram_message(text):
    with open(TELEGRAM_CONFIG, "r") as f:
        tg = json.load(f)
    bot_token = tg["bot_token"]
    chat_id = tg["chat_id"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def send_telegram_chart_with_analysis():
    with open(TELEGRAM_CONFIG, "r") as f:
        tg = json.load(f)
    bot_token = tg["bot_token"]
    chat_id = tg["chat_id"]

    if not os.path.exists(LOG_FILE):
        send_telegram_message("❌ Log file not found.")
        return

    df = pd.read_csv(LOG_FILE)
    balances = df["Balance"].tolist()
    initial = balances[0] if balances else 1000

    plt.figure()
    plt.plot(balances, marker='o')
    plt.title("Autobot Balance Over Time")
    plt.xlabel("Trade #")
    plt.ylabel("Balance")
    plt.grid(True)
    plt.savefig(CHART_FILE)
    plt.close()

    warnings = []
    if len(balances) >= 2 and balances[-1] < balances[-2]:
        warnings.append("⚠️ Profit dropped after last trade.")
    peak = max(balances)
    trough = min(balances)
    drawdown = (peak - trough) / peak
    if drawdown > 0.25:
        warnings.append(f"⚠️ Drawdown exceeds 25%: {drawdown:.2%}")
    growth = balances[-1] / initial
    if growth > 10 and len(balances) < 10:
        warnings.append(f"⚠️ Unrealistic growth: {growth:.2f}x in {len(balances)} trades.")

    caption = "📊 <b>Autobot completed</b>\n\n"
    caption += "\n".join(warnings) if warnings else "✅ No warnings. All looks good."

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(CHART_FILE, 'rb') as photo:
        requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"photo": photo})

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def run_autobot():
    print("🤖 Autobot running...")

    if not os.path.exists(CONFIG_FILE):
        print("❌ Missing logs/autobot_config.json.")
        return

    config = load_config()
    balance = config["initial_investment"]
    percent = config["daily_profit_percent"]
    trades_per_day = config["trades_per_day"]
    mode = config["mode"]
    cap_limit = config["cap_limit"]
    days = config["days"]

    withdrawn = 0
    trade_id = 1

    os.makedirs("logs", exist_ok=True)

    with open(LOG_FILE, "w") as f:
        f.write("Trade,Balance,Profit,Withdrawn\n")

    for day in range(1, days + 1):
        for trade in range(1, trades_per_day + 1):
            if os.path.exists(STOP_SIGNAL_FILE):
                send_telegram_message("🛑 Autobot stopped by /stop command.")
                os.remove(STOP_SIGNAL_FILE)
                return

            profit = balance * (percent / trades_per_day) / 100
            if mode == "reinvest":
                balance += profit
            else:
                withdrawn += profit

            with open(LOG_FILE, "a") as f:
                f.write(f"{trade_id},{balance:.2f},{profit:.2f},{withdrawn:.2f}\n")

            send_telegram_message(f"""
🔁 <b>Trade {trade_id}</b>
💰 Balance: ${balance:.2f}
📈 Profit: ${profit:.2f}
🏦 Withdrawn: ${withdrawn:.2f}
""")

            trade_id += 1
            time.sleep(2)

    send_telegram_message("✅ Autobot completed all trades.")
    send_telegram_chart_with_analysis()

if __name__ == "__main__":
    run_autobot()
