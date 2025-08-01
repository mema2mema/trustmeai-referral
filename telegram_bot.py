import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from utils import generate_summary, generate_graph

with open("telegram_config.json") as f:
    config = json.load(f)

TOKEN = config["bot_token"]

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = generate_summary()
    await update.message.reply_text(msg)

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("trade_log.csv"):
        await update.message.reply_text("No trade log available.")
        return
    await update.message.reply_document(document=open("trade_log.csv", "rb"))

async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    generate_graph()
    await update.message.reply_photo(photo=open("equity_curve.png", "rb"))

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("balance.json") as f:
        bal = json.load(f)["balance"]
    await update.message.reply_text(f"Current Balance: ${bal:.2f}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("summary", summary))
app.add_handler(CommandHandler("log", log))
app.add_handler(CommandHandler("graph", graph))
app.add_handler(CommandHandler("balance", balance))
app.run_polling()