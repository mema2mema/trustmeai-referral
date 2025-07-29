import json
import time
import os
from utils.telegram_alert import send_telegram_message

CONFIG_FILE = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"
LOG_FILE = "logs/autobot_log.csv"

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

            send_telegram_message(f"""
🔁 <b>Trade {trade_id}</b>
💰 Balance: ${balance:.2f}
📈 Profit: ${profit:.2f}
🏦 Withdrawn: ${withdrawn:.2f}
""")

            trade_id += 1
            time.sleep(2)

    send_telegram_message("✅ Autobot completed all trades.")

if __name__ == "__main__":
    run_autobot()
