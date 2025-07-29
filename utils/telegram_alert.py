import requests
import json

def load_config(config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        return json.load(file)

def send_telegram_message(message):
    config = load_config()
    bot_token = config["bot_token"]
    chat_id = config["chat_id"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Telegram error:", e)
