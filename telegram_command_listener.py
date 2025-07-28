import requests
import time
import json

def load_config(config_file='telegram_config.json'):
    with open(config_file, 'r') as file:
        return json.load(file)

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text})

def send_file(bot_token, chat_id, file_path):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(file_path, 'rb') as f:
        requests.post(url, data={'chat_id': chat_id}, files={'document': f})

def send_image(bot_token, chat_id, image_path):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    with open(image_path, 'rb') as img:
        requests.post(url, data={'chat_id': chat_id}, files={'photo': img})

def listen_for_commands():
    config = load_config()
    bot_token = config['bot_token']
    chat_id = config['chat_id']

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    last_update_id = None

    print("🤖 Bot listening for commands...")

    while True:
        response = requests.get(url).json()
        if "result" in response:
            for update in response["result"]:
                update_id = update["update_id"]
                message = update.get("message", {}).get("text", "")

                if last_update_id is None or update_id > last_update_id:
                    last_update_id = update_id

                    if message == "/summary":
                        send_message(bot_token, chat_id, "📊 Sending latest backtest summary...")
                        with open("summary.txt", "r") as file:
                            send_message(bot_token, chat_id, file.read())

                    elif message == "/log":
                        send_message(bot_token, chat_id, "📄 Sending trade log file...")
                        send_file(bot_token, chat_id, "trade_log.csv")

                    elif message == "/graph":
                        send_message(bot_token, chat_id, "📈 Sending profit chart...")
                        send_image(bot_token, chat_id, "profit_curve.png")

                    elif message == "/help":
                        send_message(bot_token, chat_id, """
🧠 *TrustMe AI Bot Commands*
/summary - Show backtest summary
/log - Download trade log CSV
/graph - Show profit chart
/help - Show command list
""")

        time.sleep(2)

if __name__ == "__main__":
    listen_for_commands()
