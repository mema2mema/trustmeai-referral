import json
import os
import time
import pandas as pd
import matplotlib.pyplot as plt
import requests  # ✅ Required for Telegram uploads
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from utils.telegram_alert import send_telegram_message

LOGS_DIR = "logs"
SIM_FILE = os.path.join(LOGS_DIR, "telegram_sim_request.json")

def run_simulation(config):
    initial = config["Initial Investment"]
    daily_percent = config["Daily Profit %"]
    days = config["Days"]
    trades_per_day = config["Trades/Day"]
    mode = config["Mode"]

    balance = initial
    withdrawn = 0
    log = []

    for day in range(1, days + 1):
        for trade in range(1, trades_per_day + 1):
            profit = balance * (daily_percent / trades_per_day) / 100
            if mode == "🔁 Reinvest":
                balance += profit
            elif mode == "💸 Withdraw":
                withdrawn += profit
            elif mode == "⚡ Withdraw Anytime":
                balance += profit  # simplified for auto-mode
            log.append((day, trade, balance, withdrawn))

    df = pd.DataFrame(log, columns=["Day", "Trade", "Balance", "Withdrawn"])
    os.makedirs(LOGS_DIR, exist_ok=True)
    df.to_csv(os.path.join(LOGS_DIR, "redhawk_trade_log.csv"), index=False)

    # Save summary.txt
    summary = f"""
📅 Days: {days}
💵 Initial Investment: ${initial}
📈 Daily Profit %: {daily_percent}
🔁 Trades/Day: {trades_per_day}
💰 Final Balance: ${balance:.2f}
💸 Total Withdrawn: ${withdrawn:.2f}
"""
    with open(os.path.join(LOGS_DIR, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary.strip())

    # Save chart
    fig, ax = plt.subplots()
    ax.plot(df["Balance"], label="Balance")
    ax.plot(df["Withdrawn"], label="Withdrawn")
    ax.set_xlabel("Trades")
    ax.set_ylabel("Amount ($)")
    ax.legend()
    chart_path = os.path.join(LOGS_DIR, "redhawk_chart.png")
    fig.savefig(chart_path)

    return summary.strip(), chart_path, os.path.join(LOGS_DIR, "redhawk_trade_log.csv")

def send_result_to_telegram(summary, chart_path, csv_path):
    send_telegram_message("📈 <b>RedHawk Auto-Simulation Complete</b>\n\n" + summary)

    # Send chart
    with open(chart_path, "rb") as img:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"photo": img}
        )

    # Send CSV
    with open(csv_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
            data={"chat_id": TELEGRAM_CHAT_ID},
            files={"document": f}
        )

def monitor_loop():
    print("📡 Auto simulation runner active...")
    while True:
        if os.path.exists(SIM_FILE):
            print("🛠️ Telegram request found. Running sim...")
            with open(SIM_FILE, "r") as f:
                config = json.load(f)
            try:
                summary, chart, csv = run_simulation(config)
                send_result_to_telegram(summary, chart, csv)
            except Exception as e:
                send_telegram_message(f"❌ Simulation failed: {e}")
            os.remove(SIM_FILE)
        time.sleep(2)

if __name__ == "__main__":
    monitor_loop()
