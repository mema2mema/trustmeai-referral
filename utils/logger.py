
import json
import requests

def send_telegram_message(message):
    try:
        with open("telegram_config.json", "r") as f:
            config = json.load(f)
        bot_token = config["bot_token"]
        chat_id = config["chat_id"]
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"[Telegram Error] Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"[Telegram Error] {e}")

if __name__ == "__main__":
    send_telegram_message("✅ TrustMe AI alert test successful!")
