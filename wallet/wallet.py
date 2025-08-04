import json
import csv
from datetime import datetime

WALLET_FILE = "wallet/wallet_data.json"
WALLET_LOG = "wallet/wallet_log.csv"

def load_wallet():
    try:
        with open(WALLET_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"balance": 0}

def save_wallet(data):
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f, indent=4)

def log_transaction(action, amount):
    with open(WALLET_LOG, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([datetime.now().isoformat(), action, amount])

def deposit(amount: float) -> str:
    wallet = load_wallet()
    wallet["balance"] += amount
    save_wallet(wallet)
    log_transaction("DEPOSIT", amount)
    return f"✅ Deposited {amount:.2f} USDT. New Balance: {wallet['balance']:.2f} USDT"

def request_withdraw(amount: float) -> tuple[str, float]:
    wallet = load_wallet()
    if amount > wallet["balance"]:
        return "❌ Insufficient balance!", wallet["balance"]
    wallet["balance"] -= amount
    save_wallet(wallet)
    log_transaction("WITHDRAW_REQUEST", amount)
    return f"📤 Withdraw request for {amount:.2f} USDT sent. New Balance: {wallet['balance']:.2f} USDT", amount

def get_balance() -> float:
    return load_wallet().get("balance", 0)