import streamlit as st
import json
import subprocess
import os
from referral_ui import register_user, show_referral_ui, get_user

BALANCE_FILE = "balance.json"
BOT_STATUS_FILE = "bot_status.json"

def get_balance():
    if not os.path.exists(BALANCE_FILE):
        return 0
    with open(BALANCE_FILE, "r") as f:
        return json.load(f).get("balance", 0)

def set_balance(amount):
    with open(BALANCE_FILE, "w") as f:
        json.dump({"balance": amount}, f)

def update_balance(amount):
    balance = get_balance()
    balance += amount
    set_balance(balance)

def get_bot_status():
    if not os.path.exists(BOT_STATUS_FILE):
        return False
    with open(BOT_STATUS_FILE, "r") as f:
        return json.load(f).get("running", False)

def set_bot_status(running):
    with open(BOT_STATUS_FILE, "w") as f:
        json.dump({"running": running}, f)

st.title("🚀 TrustMe AI Admin Panel")

query_params = st.query_params
ref = query_params.get("ref", [None])[0]
user_id = st.text_input("Enter your User ID", value="user123")
if st.button("Register"):
    register_user(user_id, referred_by=ref)
    st.success("User registered!")
    st.query_params.clear()

if get_user(user_id):
    show_referral_ui(user_id)

st.subheader("💰 Wallet")
st.write(f"Current Balance: ${get_balance():,.2f} USDT")

col1, col2 = st.columns(2)
with col1:
    deposit = st.number_input("Deposit Amount", min_value=1.0, step=1.0)
    if st.button("Deposit"):
        update_balance(deposit)
        st.success(f"Deposited ${deposit}")

with col2:
    withdraw = st.number_input("Withdraw Amount", min_value=1.0, step=1.0)
    if st.button("Withdraw"):
        if withdraw <= get_balance():
            update_balance(-withdraw)
            st.success(f"Withdrew ${withdraw}")
        else:
            st.error("Insufficient balance.")

st.subheader("🤖 Bot Controls")
running = get_bot_status()
if running:
    if st.button("🛑 Stop Bot"):
        subprocess.call(["pkill", "-f", "autobot.py"])
        set_bot_status(False)
        st.success("Bot stopped.")
else:
    if st.button("▶️ Start Bot"):
        subprocess.Popen(["python", "autobot.py"])
        set_bot_status(True)
        st.success("Bot started.")