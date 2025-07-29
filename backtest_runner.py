import csv
import time
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
from alert_utils import send_telegram_message, send_telegram_image, send_telegram_file

def run_backtest_from_csv(file_path='backtest.csv', log_file='trade_log.csv'):
    daily_profit = defaultdict(float)
    total_profit = 0
    cumulative_profit = []
    trade_labels = []
    current_profit = 0

    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        with open(log_file, 'w', newline='') as log:
            writer = csv.DictWriter(log, fieldnames=['timestamp', 'day', 'trade', 'profit', 'status'])
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
                time.sleep(2)

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
                current_profit += profit
                cumulative_profit.append(current_profit)
                trade_labels.append(f"D{day}-T{trade}")

    # Plot and send graph
    plt.figure(figsize=(10, 4))
    plt.plot(trade_labels, cumulative_profit, marker='o')
    plt.title('Cumulative Profit Curve')
    plt.xlabel('Trade')
    plt.ylabel('Profit ($)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("profit_curve.png")
    plt.close()
    send_telegram_image("profit_curve.png")

    # Build summary message
    summary = "\n📈 *Backtest Summary*\n\n"
    for day, p in daily_profit.items():
        emoji = "✅" if p >= 0 else "❌"
        summary += f"• Day {day}: ${p:.2f} {emoji}\n"
        if p < 0:
            send_telegram_message(f"⚠️ *Warning:* Day {day} ended in loss (${p:.2f}) ❌")

    summary += f"\n💰 *Total Net Profit:* ${total_profit:.2f}"
    send_telegram_message(summary)

    # Save clean summary to summary.txt
    plain_summary = "\nBacktest Summary\n\n"
    for day, p in daily_profit.items():
        status = "Profit" if p >= 0 else "Loss"
        plain_summary += f"Day {day}: ${p:.2f} ({status})\n"
    plain_summary += f"\nTotal Net Profit: ${total_profit:.2f}"

    with open("summary.txt", "w") as f:
        f.write(plain_summary)

    # Send trade log
    send_telegram_file(log_file)

# 🚀 Run it
if __name__ == "__main__":
    run_backtest_from_csv()
