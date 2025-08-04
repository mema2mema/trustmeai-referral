import os
import json
import pandas as pd
import requests
from flask import Flask, request

app = Flask(__name__)
CONFIG_PATH = "telegram_config.json"
LOG_FILE = "logs/redhawk_trade_log.csv"

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

@app.route(f"/{load_config()['bot_token']}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data:
        msg = data["message"]
        text = msg.get("text", "")
        if text == "/log":
            if os.path.exists(LOG_FILE):
                df = pd.read_csv(LOG_FILE)
                last_rows = df.tail(5).to_dict("records")
                message = "📄 Last 5 Trades:\n"
                for trade in last_rows:
                    message += f"{trade['trade_id']} | {trade['outcome']} | {trade['pnl']} USDT\n"
                send_message(message)
            else:
                send_message("❌ No trade log found.")
        elif text == "/start":
            send_message("👋 TrustMe AI Bot is live. Use /log to see latest trades.")
    return "ok"