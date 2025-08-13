import sys
import os

# Fix import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import telebot
import json
from utils.summary import generate_summary
from utils.trade_log import generate_trade_log
from utils.graph_generator import generate_graph
from utils.wallet import get_balance

# Load Telegram Config
with open("telegram_bot/telegram_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_TOKEN = config["bot_token"]
bot = telebot.TeleBot(BOT_TOKEN)

# /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.reply_to(message, "👋 Hello from TrustMe AI Telegram Bot!")

# /summary
@bot.message_handler(commands=['summary'])
def summary_handler(message):
    try:
        summary = generate_summary()
        bot.reply_to(message, f"📊 Trade Summary:\n{summary}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error in summary: {e}")

# /log
@bot.message_handler(commands=['log'])
def log_handler(message):
    try:
        log = generate_trade_log()
        bot.reply_to(message, f"📄 Recent Trade Log:\n{log}")
    except Exception as e:
        bot.reply_to(message, f"❌ Error in log: {e}")

# /balance
@bot.message_handler(commands=['balance'])
def balance_handler(message):
    try:
        balance = get_balance()
        bot.reply_to(message, f"💰 Current Wallet Balance: {balance:.2f} USDT")
    except Exception as e:
        bot.reply_to(message, f"❌ Error in balance: {e}")

# /graph
@bot.message_handler(commands=['graph'])
def graph_handler(message):
    try:
        image_path = generate_graph()
        with open(image_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo)
    except Exception as e:
        bot.reply_to(message, f"❌ Error generating graph: {e}")

# Start polling
print("✅ TrustMe AI Telegram Bot is now listening...")
bot.polling(non_stop=True)
