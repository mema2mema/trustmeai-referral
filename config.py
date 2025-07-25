# config.py

# 🔧 TrustMe AI Core Configuration
config = {
    "initial_investment": 150,
    "days": 20,
    "daily_profit_percent": 40,
    "trades_per_day": 4,
    "mode": "reinvest",  # Options: "reinvest" or "withdraw"
    "cap_limit": 250000,
    "realism": True
}

# 📡 Telegram Bot Configuration
telegram_settings = {
    "bot_token": "7702985344:AAHdsIcjcL6tvbzCk-VB90bHuaCupEEfE74",
    "chat_id": 7862868701
}

# Optional: helper accessors
TELEGRAM_BOT_TOKEN = telegram_settings["bot_token"]
TELEGRAM_CHAT_ID = telegram_settings["chat_id"]

