import requests
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.generate_summary import generate_summary
from utils.generate_graph import generate_graph
from wallet.wallet import get_balance, request_withdraw as withdraw

with open("telegram_config.json") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
CHAT_ID = config["chat_id"]

def send_withdraw_alert(amount):
    summary = generate_summary()
    graph = generate_graph()
    text = f"🚨 Withdraw Request!\nAmount: {amount:.2f} USDT\n{summary}\n{graph}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=data)