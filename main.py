import streamlit as st
import json
import os

def main():
    st.set_page_config(page_title="TrustMe AI", layout="centered")

    st.title("🚀 TrustMe AI Admin Panel")
    st.write("Welcome to your AI trading control center!")

    BALANCE_FILE = "balance.json"
    BOT_STATUS_FILE = "bot_status.json"

    # Safe JSON loader
    def load_json(path, default):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default

    # Balance functions
    def get_balance():
        return load_json(BALANCE_FILE, {"balance": 0}).get("balance", 0)

    def set_balance(amount):
        with open(BALANCE_FILE, "w") as f:
            json.dump({"balance": amount}, f)

    def update_balance(amount):
        balance = get_balance()
        balance += amount
        set_balance(balance)

    # Bot status functions
    def get_bot_status():
        return load_json(BOT_STATUS_FILE, {"running": False}).get("running", False)

    def set_bot_status(running):
        with open(BOT_STATUS_FILE, "w") as f:
            json.dump({"running": running}, f)

    # UI - Wallet
    st.subheader("💰 Wallet")
    st.write(f"Current Balance: ${get_balance():,.2f} USDT")

    col1, col2 = st.columns(2)
    with col1:
        deposit = st.number_input("Deposit Amount", min_value=1.0, step=1.0, key="deposit")
        if st.button("Deposit"):
            update_balance(deposit)
            st.success(f"Deposited ${deposit}")

    with col2:
        withdraw = st.number_input("Withdraw Amount", min_value=1.0, step=1.0, key="withdraw")
        if st.button("Withdraw"):
            if withdraw <= get_balance():
                update_balance(-withdraw)
                st.success(f"Withdrew ${withdraw}")
            else:
                st.error("Insufficient balance.")

    # UI - Bot
    st.subheader("🤖 Bot Controls (Simulation Only)")
    running = get_bot_status()
    if running:
        if st.button("🛑 Stop Bot"):
            set_bot_status(False)
            st.success("Bot stopped (simulation only).")
    else:
        if st.button("▶️ Start Bot"):
            set_bot_status(True)
            st.success("Bot started (simulation only).")

    # Visual indicator
    st.info("🔄 Bot is currently: **{}**".format("Running" if get_bot_status() else "Stopped"))


# Run when called from Streamlit or elsewhere
if __name__ == "__main__":
    main()
