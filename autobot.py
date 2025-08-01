import time
import pandas as pd
import random
import os
import json
from datetime import datetime

LOG_FILE = "trade_log.csv"
BALANCE_FILE = "balance.json"

def get_balance():
    if not os.path.exists(BALANCE_FILE):
        return 0
    with open(BALANCE_FILE, "r") as f:
        return json.load(f).get("balance", 0)

def update_balance(amount):
    balance = get_balance()
    balance += amount
    with open(BALANCE_FILE, "w") as f:
        json.dump({"balance": balance}, f)

def log_trade(pnl):
    now = datetime.now()
    row = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "pnl": pnl
    }
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame([row])
    else:
        df = pd.read_csv(LOG_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False)

while True:
    pnl = round(random.uniform(-5, 10), 2)
    update_balance(pnl)
    log_trade(pnl)
    time.sleep(10)