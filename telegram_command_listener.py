import requests
import time
import json
import os

CONFIG_FILE = "telegram_config.json"
AUTOBOT_CONFIG = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text})

def send_file(bot_token, chat_id, file_path, file_type="document"):
    url = f"https://api.telegram.org/bot{bot_token}/send{file_type.capitalize()}"
    with open(file_path, "rb") as f:
        requests.post(url, data={'chat_id': chat_id}, files={file_type.lower(): f})

def get_updates(bot_token, offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    if offset:
        url += f"?offset={offset}"
    return requests.get(url).json()

def parse_autobot_command(text):
    try:
        parts = text.strip().split()
        if len(parts) == 7 and parts[0] == "/autobot":
            return {
                "initial_investment": float(parts[1]),
                "daily_profit_percent": float(parts[2]),
                "mode": parts[3].lower(),
                "trades_per_day": int(parts[4]),
                "cap_limit": float(parts[5]),
                "days": int(parts[6]),
            }
    except:
        return None
    return None

def listen_for_commands():
    config = load_config()
    bot_token = config['bot_token']
    chat_id = config['chat_id']
    last_update_id = None

    print("🤖 TrustMe AI bot is now listening...")

    while True:
        updates = get_updates(bot_token, offset=last_update_id)
        for update in updates.get("result", []):
            message = update.get("message", {})
            text = message.get("text", "")
            update_id = update["update_id"]

            if update_id != last_update_id:
                print(f"📩 Command: {text}")

                if text.startswith("/summary"):
                    try:
                        send_file(bot_token, chat_id, "logs/summary.txt", file_type="document")
                    except:
                        send_message(bot_token, chat_id, "❌ summary.txt not found.")

                elif text.startswith("/log"):
                    try:
                        send_file(bot_token, chat_id, "logs/redhawk_trade_log.csv", file_type="document")
                    except:
                        send_message(bot_token, chat_id, "❌ trade_log.csv not found.")

                elif text.startswith("/graph"):
                    try:
                        send_file(bot_token, chat_id, "logs/redhawk_chart.png", file_type="photo")
                    except:
                        send_message(bot_token, chat_id, "❌ redhawk_chart.png not found.")

                elif text.startswith("/help"):
                    send_message(bot_token, chat_id, """
🧠 <b>TrustMe AI Commands</b>
/summary – View last summary.txt
/log – Download trade log CSV
/graph – View growth chart
/autobot 150 35 reinvest 3 300 75 – Start bot
/stop – Stop running bot
/help – Show this help message
                    """.strip())

                elif text.startswith("/stop"):
                    with open(STOP_SIGNAL_FILE, "w") as f:
                        f.write("stop")
                    send_message(bot_token, chat_id, "🛑 Autobot has been stopped.")

                elif text.startswith("/autobot"):
                    autobot_config = parse_autobot_command(text)
                    if autobot_config:
                        with open(AUTOBOT_CONFIG, "w") as f:
                            json.dump(autobot_config, f, indent=2)
                        send_message(bot_token, chat_id, "✅ Autobot config saved. Run it in VSCode now.")
                    else:
                        send_message(bot_token, chat_id, "❌ Invalid /autobot command format.")

                last_update_id = update_id + 1
        time.sleep(2)

if __name__ == "__main__":
    listen_for_commands()
