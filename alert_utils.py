import json
import requests

def load_telegram_config(config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config['bot_token'], config['chat_id']

def send_telegram_message(message, config_file='telegram_config.json'):
    bot_token, chat_id = load_telegram_config(config_file)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    return response.ok
