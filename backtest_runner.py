import csv
from alert_utils import send_telegram_message
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import requests
import json
import time

def send_telegram_image(image_path, config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    bot_token = config['bot_token']
    chat_id = config['chat_id']

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id}, files={'photo': photo})

def send_telegram_file(file_path, config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    bot_token = config['bot_token']
    chat_id = config['chat_id']

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, 'rb') as doc:
        requests.post(url, data={'chat_id': chat_id}, files={'document': doc})

def run_backtest_from_csv(file_path='backtest.csv', log_file='trade_log.csv'):
    daily_profit = defaultdict(float)
    total_profit = 0
    cumulative_profit = []
    trade_labels = []

    current_profit = 0
    trade_counter = 0

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)

        with open(log_file, 'w', newline='') as log:
            fieldnames = ['timestamp', 'day', 'trade', 'profit', 'status']
            writer = csv.DictWriter(log, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                day = row['day']
                trade = row['trade']
                profit = float(row['profit'])
                status = "Profit" if profit >= 0 else "Loss"
                emoji = "✅" if profit >= 0 else "❌"

                message = f"""
📊 *Backtest Day {day} — Trade {trade}*
*Profit:* ${profit} {emoji}
"""
                print(f"[BACKTEST] Day {day}, Trade {trade} — Profit: {profit}")
                send_telegram_message(message)

                time.sleep(2)  # 🔁 Replay delay (2 seconds between trades)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow({
                    'timestamp': timestamp,
                    'day': day,
                    'trade': trade,
                    'profit': profit,
                    'status': status
                })

                daily_profit[day] += profit
                total_profit += profit
                trade_counter += 1
                current_profit += profit
                cumulative_profit.append(current_profit)
                trade_labels.append(f"D{day}-T{trade}")

    # 📈 Profit graph
    plt.figure(figsize=(10, 4))
    plt.plot(trade_labels, cumulative_profit, marker='o')
    plt.title('Cumulative Profit Curve')
    plt.xlabel('Trade')
    plt.ylabel('Profit ($)')
    plt.grid(True)
    plt.tight_layout()
    graph_path = 'profit_curve.png'
    plt.savefig(graph_path)
    plt.close()

    send_telegram_image(graph_path)

    # 📬 Summary report
    summary = "\n📈 *Backtest Summary*\n\n"
    for day, p in daily_profit.items():
        emoji = "✅" if p >= 0 else "❌"
        summary += f"• Day {day}: ${p:.2f} {emoji}\n"

        if p < 0:
            warning = f"⚠️ *Warning:* Day {day} ended in a net loss of ${p:.2f} ❌"
            send_telegram_message(warning)

    summary += f"\n💰 *Total Net Profit:* ${total_profit:.2f}"
    print("[BACKTEST] Sending summary...")
    send_telegram_message(summary)

    # 📤 Send CSV log to Telegram
    send_telegram_file(log_file)

# 🚀 Run
run_backtest_from_csv()
