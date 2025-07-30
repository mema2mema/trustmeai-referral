
import subprocess
import os
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

TELEGRAM_BOT_TOKEN = "7702985344:AAHdsIcjcL6tvbzCk-VB90bHuaCupEEfE74"
AUTOBOT_CONFIG = "logs/autobot_config.json"
STOP_SIGNAL_FILE = "logs/autobot_stop.signal"

# /autobot command handler
def handle_autobot(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) != 6:
            raise ValueError("Invalid number of arguments.")

        config = {
            "initial_investment": float(args[0]),
            "daily_profit_percent": float(args[1]),
            "mode": args[2],
            "trades_per_day": int(args[3]),
            "cap_limit": float(args[4]),
            "days": int(args[5])
        }

        os.makedirs("logs", exist_ok=True)
        with open(AUTOBOT_CONFIG, "w") as f:
            json.dump(config, f, indent=2)

        update.message.reply_text("✅ Autobot config saved. Launching...")

        subprocess.Popen(["python", "autobot.py"])

    except Exception as e:
        update.message.reply_text("❌ Usage: /autobot <amount> <profit%> <mode> <trades/day> <cap> <days>")

# /stop handler
def handle_stop(update: Update, context: CallbackContext):
    with open(STOP_SIGNAL_FILE, "w") as f:
        f.write("STOP")
    update.message.reply_text("🛑 Stop signal sent to Autobot.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("autobot", handle_autobot))
    dp.add_handler(CommandHandler("stop", handle_stop))

    updater.start_polling()

if __name__ == "__main__":
    main()
