import streamlit as st
import json
import os

st.set_page_config(page_title="TrustMe AI", layout="centered")

st.title("🚀 TrustMe AI Admin Panel")
st.write("Welcome to your AI trading control center!")

BALANCE_FILE = "balance.json"
BOT_STATUS_FILE = "bot_status.json"

def get_balance():
    if not os.path.exists(BALANCE_FILE):
        return 0.0
    try:
        with open(BALANCE_FILE, "r") as f:
            return float(json.load(f).get("balance", 0.0))
    except:
        return 0.0

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
    try:
        with open(BOT_STATUS_FILE, "r") as f:
            return json.load(f).get("running", False)
    except:
        return False

def set_bot_status(running):
    with open(BOT_STATUS_FILE, "w") as f:
        json.dump({"running": running}, f)

# Wallet Section
st.subheader("💰 Wallet")
st.write(f"Current Balance: **${get_balance():,.2f} USDT**")

col1, col2 = st.columns(2)
with col1:
    deposit = st.number_input("Deposit Amount", min_value=1.0, step=1.0)
    if st.button("Deposit"):
        update_balance(deposit)
        st.success(f"✅ Deposited ${deposit:.2f}")

with col2:
    withdraw = st.number_input("Withdraw Amount", min_value=1.0, step=1.0)
    if st.button("Withdraw"):
        if withdraw <= get_balance():
            update_balance(-withdraw)
            st.success(f"✅ Withdrew ${withdraw:.2f}")
        else:
            st.error("❌ Insufficient balance")

# Bot Status Simulation Only (No actual start/stop)
st.subheader("🤖 Bot Controls (Simulation Only)")
running = get_bot_status()
if running:
    if st.button("🛑 Stop Bot"):
        set_bot_status(False)
        st.success("Bot status set to STOPPED.")
else:
    if st.button("▶️ Start Bot"):
        set_bot_status(True)
        st.success("Bot status set to RUNNING.")