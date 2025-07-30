import requests
import json

with open("telegram_config.json", "r") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
CHAT_ID = config["chat_id"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram message failed:", e)

def send_telegram_file(file_path, file_type="document"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/send{file_type.capitalize()}"
    with open(file_path, "rb") as f:
        try:
            requests.post(url, data={"chat_id": CHAT_ID}, files={file_type.lower(): f})
        except Exception as e:
            print("Telegram file send failed:", e)
