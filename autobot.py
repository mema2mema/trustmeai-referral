# autobot.py

import matplotlib.pyplot as plt
import json
import requests
from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

initial_balance = 1000
balance = initial_balance
balance_log = [balance]
profit_log = []
drawdown_threshold = 0.25

def send_telegram_photo(photo_path, caption="Autobot run complete 📊"):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption}, files={"photo": photo})

def check_ai_warnings(balance_log):
    warnings = []
    if len(balance_log) < 2:
        return warnings

    # 1. Profit drop check
    if balance_log[-1] < balance_log[-2]:
        warnings.append("⚠️ Profit dropped after last trade.")

    # 2. Drawdown check
    peak = max(balance_log)
    trough = min(balance_log)
    drawdown = (peak - trough) / peak
    if drawdown > drawdown_threshold:
        warnings.append(f"⚠️ Drawdown exceeds 25%: {drawdown:.2%}")

    # 3. Unrealistic compound growth check
    growth = balance_log[-1] / initial_balance
    if growth > 10 and len(balance_log) < 10:
        warnings.append(f"⚠️ Unrealistic growth detected: {growth:.2f}x in {len(balance_log)} trades.")

    return warnings

def simulate_trades(trade_returns):
    global balance
    for i, profit_pct in enumerate(trade_returns):
        profit = balance * profit_pct
        balance += profit
        balance_log.append(balance)
        profit_log.append(profit)

    # Plot the chart
    plt.figure()
    plt.plot(balance_log, marker='o')
    plt.title("Autobot Balance Over Time")
    plt.xlabel("Trade #")
    plt.ylabel("Balance")
    plt.grid(True)
    plt.savefig("autobot_chart.png")
    plt.close()

    # AI warning system
    warnings = check_ai_warnings(balance_log)
    warning_text = "\n".join(warnings) if warnings else "✅ No warnings. All looks good."

    # Send chart and summary to Telegram
    send_telegram_photo("autobot_chart.png", caption=f"📊 Autobot session complete.\n\n{warning_text}")

if __name__ == "__main__":
    # Simulated trade returns (as % gain/loss per trade)
    trades = [0.05, 0.03, -0.02, 0.04, -0.15, 0.1, 0.07, 0.02]
    simulate_trades(trades)
