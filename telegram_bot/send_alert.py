import requests
import json
import os

CONFIG_PATH = "telegram_config.json"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def send_message(text):
    config = load_config()
    token = config["bot_token"]
    chat_id = config["chat_id"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def send_withdraw_alert(amount):
    send_message(f"📤 Withdraw request for {amount:.2f} USDT")

def send_trade_alert(trade):
    msg = (
        f"✅ Trade Executed!\n"
        f"ID: {trade['trade_id']}\n"
        f"Amount: {trade['amount']} USDT\n"
        f"Outcome: {trade['outcome']}\n"
        f"PnL: {trade['pnl']} USDT"
    )
    send_message(msg)