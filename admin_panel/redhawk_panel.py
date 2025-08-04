import streamlit as st
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from redhawk_engine import run_redhawk_trade, init_log

LOG_FILE = "logs/redhawk_trade_log.csv"

st.title("🧠 RedHawk 2.0 High-Win Trade Simulator")

# Inputs
st.subheader("📊 Simulation Settings")
num_trades = st.slider("Number of Trades", min_value=1, max_value=20, value=5)
trade_amount = st.number_input("Amount per Trade (USDT)", min_value=10.0, value=1000.0)
win_rate = st.slider("Win Rate", min_value=0.0, max_value=1.0, value=0.9)
risk_percent = st.slider("Risk % on Loss", min_value=1, max_value=50, value=10)

# Run trades
if st.button("🚀 Run RedHawk Simulation"):
    init_log()
    for i in range(1, num_trades + 1):
        result = run_redhawk_trade(trade_id=f"RH-{i:03}", amount=trade_amount, win_rate=win_rate, risk_percent=risk_percent)
        st.json(result)

# Show recent log
if os.path.exists(LOG_FILE):
    st.subheader("📄 Recent Trade Log")
    df = pd.read_csv(LOG_FILE, on_bad_lines="skip")
    st.dataframe(df.tail(10))