
import time
from utils.logger import send_telegram_message

def run_strategy(daily_profit_percent, reinvest_enabled, reinvest_frequency):
    investment = 100  # Starting capital
    total_profit = 0

    for i in range(5):  # Simulate 5 trades
        profit = investment * (daily_profit_percent / 100)
        total_profit += profit

        log_message = f"📈 Trade {i+1}: Profit = ${profit:.2f}, Total = ${total_profit:.2f}"
        send_telegram_message(log_message)

        if reinvest_enabled:
            investment += profit
            send_telegram_message(f"🔁 Auto Reinvest Enabled: New capital = ${investment:.2f}")
        else:
            send_telegram_message(f"💰 Profit Withdrawn: ${profit:.2f}")

        time.sleep(reinvest_frequency)  # Simulated wait

if __name__ == "__main__":
    run_strategy(daily_profit_percent=10, reinvest_enabled=True, reinvest_frequency=2)
