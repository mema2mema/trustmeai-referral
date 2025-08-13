
import os
import json

WALLET_FILE = os.path.join(os.path.dirname(__file__), "wallet.json")

def load_wallet():
    if not os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "w", encoding="utf-8") as f:
            json.dump({"balance": 0}, f)
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallet(data):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def deposit(amount):
    wallet = load_wallet()
    wallet["balance"] += amount
    save_wallet(wallet)
    return wallet["balance"]

def withdraw(amount):
    wallet = load_wallet()
    if amount > wallet["balance"]:
        return False, wallet["balance"]
    wallet["balance"] -= amount
    save_wallet(wallet)
    return True, wallet["balance"]

def get_balance():
    wallet = load_wallet()
    return wallet["balance"]

def request_withdraw(amount):
    success, balance = withdraw(amount)
    if success:
        return f"✅ Withdraw request for {amount:.2f} USDT sent. New Balance: {balance:.2f} USDT", amount
    else:
        return f"❌ Insufficient balance. Current Balance: {balance:.2f} USDT", 0
