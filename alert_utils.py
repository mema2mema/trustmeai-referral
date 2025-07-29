import json
import requests

def load_telegram_config(config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        return json.load(file)

def send_telegram_message(message):
    config = load_telegram_config()
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    payload = {
        "chat_id": config['chat_id'],
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def send_telegram_image(image_path):
    config = load_telegram_config()
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendPhoto"
    with open(image_path, 'rb') as img:
        requests.post(url, data={'chat_id': config['chat_id']}, files={'photo': img})

def send_telegram_file(file_path):
    config = load_telegram_config()
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendDocument"
    with open(file_path, 'rb') as doc:
        requests.post(url, data={'chat_id': config['chat_id']}, files={'document': doc})
