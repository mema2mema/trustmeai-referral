import requests
import time
import json

def load_config(config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        return json.load(file)

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text})

def get_updates(bot_token, offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    if offset:
        url += f"?offset={offset}"
    return requests.get(url).json()

def listen_for_commands():
    config = load_config()
    bot_token = config['bot_token']
    chat_id = config['chat_id']
    last_update_id = None

    print("🤖 Bot is listening for commands...")

    while True:
        updates = get_updates(bot_token, offset=last_update_id)
        for update in updates.get("result", []):
            message = update.get("message", {})
            text = message.get("text", "")
            update_id = update["update_id"]

            if update_id != last_update_id:
                print(f"[COMMAND RECEIVED] {text}")

                if text == "/summary":
                    try:
                        with open("summary.txt", "r") as file:
                            send_message(bot_token, chat_id, file.read())
                    except:
                        send_message(bot_token, chat_id, "❌ summary.txt not found.")

                elif text == "/log":
                    try:
                        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                        with open("trade_log.csv", "rb") as f:
                            requests.post(url, data={'chat_id': chat_id}, files={'document': f})
                    except:
                        send_message(bot_token, chat_id, "❌ trade_log.csv not found.")

                elif text == "/graph":
                    try:
                        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                        with open("profit_curve.png", "rb") as img:
                            requests.post(url, data={'chat_id': chat_id}, files={'photo': img})
                    except:
                        send_message(bot_token, chat_id, "❌ profit_curve.png not found.")

                elif text == "/help":
                    send_message(bot_token, chat_id, """
📟 *TrustMe AI Bot Commands*
/summary - View last backtest summary
/log - Download trade log
/graph - View profit chart
/help - Show this menu
""")

                last_update_id = update_id + 1

        time.sleep(2)

if __name__ == "__main__":
    listen_for_commands()
