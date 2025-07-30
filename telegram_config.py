import json

with open("telegram_config.json", "r") as f:
    config = json.load(f)

TELEGRAM_BOT_TOKEN = config["bot_token"]
TELEGRAM_CHAT_ID = config["chat_id"]
