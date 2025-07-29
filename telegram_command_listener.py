import requests
import time
import json
import os
import pandas as pd
import matplotlib.pyplot as plt

CONFIG_FILE = "telegram_config.json"
AUTOBOT_CONFIG = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"
LOG_FILE = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"

def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'})

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
        print(f"🧪 DEBUG: Parsed parts = {parts}")  # Debug log

        if parts[0] != "/autobot":
            return None

        if len(parts) != 7:
            return f"❌ Format Error: 7 parts required (including /autobot), got {len(parts)}"

        config = {
            "initial_investment": float(parts[1]),
            "daily_profit_percent": float(parts[2]),
            "mode": parts[3].lower(),
            "trades_per_day": int(parts[4]),
            "cap_limit": float(parts[5]),
            "days": int(parts[6]),
        }

        return config
    except Exception as e:
        return f"❌ Error parsing command: {str(e)}"

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
                print(f"📩 Command Received: {text}")

                if text.startswith("/autobot"):
                    result = parse_autobot_command(text)
                    if isinstance(result, dict):
                        with open(AUTOBOT_CONFIG, "w") as f:
                            json.dump(result, f, indent=2)
                        send_message(bot_token, chat_id, "✅ Autobot config saved. Run it in VSCode now.")
                    else:
                        send_message(bot_token, chat_id, str(result))

                elif text.startswith("/stop"):
                    with open(STOP_SIGNAL_FILE, "w") as f:
                        f.write("stop")
                    send_message(bot_token, chat_id, "🛑 Autobot has been stopped by user.")

                elif text.startswith("/analyze"):
                    try:
                        if not os.path.exists(LOG_FILE):
                            send_message(bot_token, chat_id, "❌ autobot_log.csv not found.")
                            continue

                        df = pd.read_csv(LOG_FILE)
                        balances = df["Balance"].tolist()
                        initial = balances[0] if balances else 1000

                        plt.figure()
                        plt.plot(balances, marker='o')
                        plt.title("Autobot Balance Over Time")
                        plt.xlabel("Trade #")
                        plt.ylabel("Balance")
                        plt.grid(True)
                        plt.savefig(CHART_FILE)
                        plt.close()

                        warnings = []
                        if len(balances) >= 2 and balances[-1] < balances[-2]:
                            warnings.append("⚠️ Profit dropped after last trade.")
                        peak = max(balances)
                        trough = min(balances)
                        drawdown = (peak - trough) / peak
                        if drawdown > 0.25:
                            warnings.append(f"⚠️ Drawdown exceeds 25%: {drawdown:.2%}")
                        growth = balances[-1] / initial
                        if growth > 10 and len(balances) < 10:
                            warnings.append(f"⚠️ Unrealistic growth: {growth:.2f}x in {len(balances)} trades.")

                        caption = "📊 <b>Autobot Analysis</b>\n\n"
                        caption += "\n".join(warnings) if warnings else "✅ No warnings. All looks good."

                        send_file(bot_token, chat_id, CHART_FILE, file_type="photo")
                        send_message(bot_token, chat_id, caption)
                    except Exception as e:
                        send_message(bot_token, chat_id, f"❌ Error in /analyze: {str(e)}")

                elif text.startswith("/help"):
                    send_message(bot_token, chat_id, """
🧠 <b>TrustMe AI Commands</b>
/autobot 150 35 reinvest 3 300 75 – Save config
/stop – Stop the bot
/analyze – Run AI chart + warnings
/help – Show this message
                    """.strip())

                last_update_id = update_id + 1
        time.sleep(2)

if __name__ == "__main__":
    listen_for_commands()
