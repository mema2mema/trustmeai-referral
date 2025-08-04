import csv
import random
from datetime import datetime

LOG_FILE = "logs/redhawk_trade_log.csv"

# Create CSV with headers if not exists
def init_log():
    try:
        with open(LOG_FILE, "x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "trade_id", "amount", "result", "pnl"])
    except FileExistsError:
        pass

def run_redhawk_trade(trade_id, amount, win_rate=0.9, risk_percent=10):
    # Determine win or loss
    outcome = "WIN" if random.random() < win_rate else "LOSS"

    if outcome == "WIN":
        pnl = round(amount * 0.15, 2)  # 15% profit
    else:
        pnl = round(-amount * (risk_percent / 100), 2)  # controlled loss

    timestamp = datetime.now().isoformat()

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, trade_id, amount, outcome, pnl])

    return {
        "trade_id": trade_id,
        "timestamp": timestamp,
        "amount": amount,
        "outcome": outcome,
        "pnl": pnl
    }

# Example runner
if __name__ == "__main__":
    init_log()
    for i in range(1, 6):
        result = run_redhawk_trade(trade_id=f"RH-{i:03}", amount=1000)
        print(result)