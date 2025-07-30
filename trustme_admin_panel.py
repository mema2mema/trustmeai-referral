import os
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from utils.telegram_alert import send_telegram_message, send_telegram_file
import json
import streamlit as st

SUMMARY_FILE = "logs/summary.txt"
LOG_FILE = "logs/autobot_log.csv"
CHART_FILE = "logs/autobot_chart.png"
WALLET_FILE = "logs/wallet.json"

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Load or initialize wallet
if not os.path.exists(WALLET_FILE):
    with open(WALLET_FILE, "w") as f:
        json.dump({"balance": 0}, f)

def load_wallet():
    with open(WALLET_FILE, "r") as f:
        return json.load(f)

def save_wallet(data):
    with open(WALLET_FILE, "w") as f:
        json.dump(data, f)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 TrustMe AI is live! Send /help for commands.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("""
🧠 TrustMe AI Commands:
/autobot <amt> <profit%> <mode> <trades> <cap> <days>
/stop – Stop Autobot
/log – Get trade log CSV
/graph – Get final chart
/summary – Get AI summary
/analyze – Chart + Log + AI report
/help – Show this help
/deposit <amount>
/withdraw <amount>
/balance
""")

def stop_command(update: Update, context: CallbackContext):
    with open("logs/autobot_stop.signal", "w") as f:
        f.write("stop")
    update.message.reply_text("🛑 Autobot stopped.")

def summary_command(update: Update, context: CallbackContext):
    if os.path.exists(SUMMARY_FILE):
        send_telegram_file(SUMMARY_FILE, file_type="document")
    else:
        update.message.reply_text("❌ summary.txt not found.")

def graph_command(update: Update, context: CallbackContext):
    if os.path.exists(CHART_FILE):
        send_telegram_file(CHART_FILE, file_type="photo")
    else:
        update.message.reply_text("❌ Chart not found.")

def log_command(update: Update, context: CallbackContext):
    if os.path.exists(LOG_FILE):
        send_telegram_file(LOG_FILE, file_type="document")
    else:
        update.message.reply_text("❌ Log not found.")

def analyze_command(update: Update, context: CallbackContext):
    try:
        if os.path.exists(CHART_FILE):
            send_telegram_file(CHART_FILE, file_type="photo")
        if os.path.exists(LOG_FILE):
            send_telegram_file(LOG_FILE, file_type="document")

            df = pd.read_csv(LOG_FILE)
            peak = df["Balance"].max()
            low = df["Balance"].min()
            drawdown = peak - low
            gain = df["Balance"].iloc[-1] - df["Balance"].iloc[0]
            risky = drawdown > (peak * 0.25)

            summary = f"""
📈 FINAL REPORT
--------------------------
Total Trades: {len(df)}
Final Balance: ${df['Balance'].iloc[-1]:.2f}
Total Profit: ${gain:.2f}
Max Drawdown: ${drawdown:.2f}
Risk Level: {'⚠️ HIGH' if risky else '✅ Safe'}
""".strip()

            with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
                f.write(summary)

            send_telegram_file(SUMMARY_FILE, file_type="document")
            send_telegram_message("✅ /analyze complete: chart, log, and summary sent.")
        else:
            send_telegram_message("⚠️ No autobot log found.")
    except Exception as e:
        send_telegram_message(f"❌ Analyze error: {e}")

def deposit(update: Update, context: CallbackContext):
    try:
        amount = float(context.args[0])
        wallet = load_wallet()
        wallet["balance"] += amount
        save_wallet(wallet)
        update.message.reply_text(f"💰 Deposited: {amount} USDT\nNew Balance: {wallet['balance']} USDT")
    except:
        update.message.reply_text("❌ Usage: /deposit <amount>")

def withdraw(update: Update, context: CallbackContext):
    try:
        amount = float(context.args[0])
        wallet = load_wallet()
        if wallet["balance"] >= amount:
            wallet["balance"] -= amount
            save_wallet(wallet)
            update.message.reply_text(f"✅ Withdrawn: {amount} USDT\nRemaining Balance: {wallet['balance']} USDT")
        else:
            update.message.reply_text("❌ Insufficient balance.")
    except:
        update.message.reply_text("❌ Usage: /withdraw <amount>")

def check_balance(update: Update, context: CallbackContext):
    wallet = load_wallet()
    update.message.reply_text(f"👛 Your Wallet Balance: {wallet['balance']} USDT")

def main():
    from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stop", stop_command))
    dp.add_handler(CommandHandler("log", log_command))
    dp.add_handler(CommandHandler("graph", graph_command))
    dp.add_handler(CommandHandler("summary", summary_command))
    dp.add_handler(CommandHandler("analyze", analyze_command))
    dp.add_handler(CommandHandler("deposit", deposit))
    dp.add_handler(CommandHandler("withdraw", withdraw))
    dp.add_handler(CommandHandler("balance", check_balance))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
