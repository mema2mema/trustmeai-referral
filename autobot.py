# File: autobot.py (Final Auto-Send Integration)

import json
import time
import os
import pandas as pd
import matplotlib.pyplot as plt
from utils.telegram_alert import send_telegram_message, send_telegram_file

CONFIG_FILE = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"
LOG_FILE = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"

# Load config
def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def run_autobot():
    print("🤖 Autobot running...")

    if not os.path.exists(CONFIG_FILE):
        print("❌ Missing logs/autobot_config.json. Please send /autobot from Telegram first.")
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
                send_telegram_message("🛑 Autobot stopped by /stop")
                os.remove(STOP_SIGNAL_FILE)
                return

            profit = balance * (percent / trades_per_day) / 100
            if mode == "reinvest":
                balance += profit
            else:
                withdrawn += profit

            with open(LOG_FILE, "a") as f:
                f.write(f"{trade_id},{balance:.2f},{profit:.2f},{withdrawn:.2f}\n")

            trade_id += 1
            time.sleep(0.01)  # Super fast for testing


    # Generate chart after final trade
    df = pd.read_csv(LOG_FILE)
    if len(df) > 0:
        plt.figure(figsize=(10, 4))
        plt.plot(df["Trade"], df["Balance"], marker="o")
        plt.title("Autobot Final Balance Chart")
        plt.xlabel("Trade")
        plt.ylabel("Balance")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(CHART_FILE)

        # Send completion alert to Telegram
        send_telegram_message("✅ Autobot has completed all trades. Final report attached:")
        send_telegram_file(CHART_FILE, file_type="photo")
        send_telegram_file(LOG_FILE, file_type="document")
    else:
        send_telegram_message("⚠️ Autobot completed but no trades were logged.")

if __name__ == "__main__":
    run_autobot()
