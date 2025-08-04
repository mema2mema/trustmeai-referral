import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wallet.wallet import deposit, request_withdraw, get_balance
from telegram_bot.send_alert import send_withdraw_alert

st.header("💰 Mock Wallet System (USDT)")

# View balance
balance = get_balance()
st.success(f"Current Balance: {balance:.2f} USDT")

# Deposit form
st.subheader("➕ Deposit USDT")
deposit_amt = st.number_input("Enter amount to deposit", min_value=1.0)
if st.button("Deposit"):
    msg = deposit(deposit_amt)
    st.success(msg)

# Withdraw form
st.subheader("📤 Withdraw USDT")
withdraw_amt = st.number_input("Enter amount to withdraw", min_value=1.0)
if st.button("Request Withdraw"):
    msg, amount = request_withdraw(withdraw_amt)
    st.info(msg)
    if "Withdraw request for" in msg:
        send_withdraw_alert(amount)