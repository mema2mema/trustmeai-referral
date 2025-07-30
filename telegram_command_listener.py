# File: telegram_command_listener.py

import requests
import time
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from utils.telegram_alert import send_telegram_message, send_telegram_file

CONFIG_FILE = "telegram_config.json"
AUTOBOT_LOG = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"

# Load bot token and chat ID
def load_telegram_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_updates(bot_token, offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    if offset:
        url += f"?offset={offset}"
    return requests.get(url).json()

def listen_for_commands():
    config = load_telegram_config()
    bot_token = config['bot_token']
    chat_id = config['chat_id']
    last_update_id = None

    print("🤖 Listening for Telegram commands...")

    while True:
        updates = get_updates(bot_token, offset=last_update_id)
        for update in updates.get("result", []):
            message = update.get("message", {})
            text = message.get("text", "")
            update_id = update["update_id"]

            if update_id != last_update_id:
                print(f"📩 Command: {text}")

                if text.startswith("/analyze"):
                    if os.path.exists(AUTOBOT_LOG):
                        df = pd.read_csv(AUTOBOT_LOG)
                        if len(df) > 0:
                            plt.figure(figsize=(10, 4))
                            plt.plot(df["Trade"], df["Balance"], marker='o')
                            plt.title("Autobot Performance")
                            plt.xlabel("Trade")
                            plt.ylabel("Balance")
                            plt.grid(True)
                            plt.tight_layout()
                            plt.savefig(CHART_FILE)
                            send_telegram_message("📈 Autobot Analysis Completed:")
                            send_telegram_file(CHART_FILE, file_type="photo")
                            send_telegram_file(AUTOBOT_LOG, file_type="document")
                        else:
                            send_telegram_message("⚠️ Log is empty. No trades yet.")
                    else:
                        send_telegram_message("⚠️ No log file found.")

                elif text.startswith("/stop"):
                    with open(STOP_SIGNAL_FILE, "w") as f:
                        f.write("stop")
                    send_telegram_message("🛑 Bot stopped.")

                last_update_id = update_id + 1

        time.sleep(2)

if __name__ == "__main__":
    listen_for_commands()
