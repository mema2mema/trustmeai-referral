import streamlit as st
import pandas as pd
import sys
import os
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.strategy import run_redhawk_strategy
from utils.config import config
from utils.logger import setup_logger
from backtest import run_csv_backtest

st.set_page_config(page_title="RedHawk Dashboard", layout="wide")
st.title("🦅 RedHawk Profit Simulator")

logger = setup_logger()

# === Realtime Simulation ===
st.sidebar.header("⚙️ Live Simulation Settings")
initial_investment = st.sidebar.slider("💰 Initial Investment ($)", 10, 100000, 150)
days = st.sidebar.slider("📅 Simulation Days", 1, 365, 20)
daily_profit_percent = st.sidebar.slider("📈 Daily Profit (%)", 1, 100, 40)
trades_per_day = st.sidebar.slider("🔄 Trades per Day", 1, 10, 4)
mode = st.sidebar.selectbox("💼 Profit Mode", ["Reinvest", "Withdraw"])

if st.button("▶️ Run Simulation"):
    config["initial_investment"] = initial_investment
    config["days"] = days
    config["daily_profit_percent"] = daily_profit_percent
    config["trades_per_day"] = trades_per_day
    config["mode"] = mode.lower()

    history, trade_log, summary = run_redhawk_strategy(config, logger)

    st.success("✅ Simulation Complete")
    st.json(summary)

    hist_df = pd.DataFrame(history)
    log_df = pd.DataFrame(trade_log)

    st.subheader("📊 Daily Summary")
    st.dataframe(hist_df, use_container_width=True)

    csv_hist = hist_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Daily Summary CSV", csv_hist, "daily_summary.csv", "text/csv")

    # Chart
    st.subheader("📈 Balance Growth Chart")
    fig, ax = plt.subplots()
    ax.plot(hist_df['day'], hist_df['end_balance'], marker='o')
    ax.set_xlabel("Day")
    ax.set_ylabel("Balance ($)")
    ax.set_title("RedHawk Balance Over Time")
    st.pyplot(fig)

    st.subheader("🧾 Trade Log")
    st.dataframe(log_df, use_container_width=True)

    csv_log = log_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Trade Log CSV", csv_log, "trade_log.csv", "text/csv")

# === CSV Upload & Backtest ===
st.markdown("---")
st.header("📁 CSV Backtest")

uploaded_file = st.file_uploader("Upload a trade log CSV (day, trade, profit)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.dropna()

    st.subheader("🔍 Uploaded Trade Log")
    st.dataframe(df, use_container_width=True)

    history, trade_log, summary = run_csv_backtest(uploaded_file)

    if summary:
        st.success("✅ CSV Backtest Complete")
        st.json(summary)

        hist_df = pd.DataFrame(history)
        log_df = pd.DataFrame(trade_log)

        st.subheader("📊 Backtest Daily Summary")
        st.dataframe(hist_df, use_container_width=True)

        csv_hist = hist_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Daily Summary CSV", csv_hist, "backtest_summary.csv", "text/csv")

        # Chart
        st.subheader("📈 Backtest Balance Growth Chart")
        fig, ax = plt.subplots()
        ax.plot(hist_df['day'], hist_df['end_balance'], marker='o')
        ax.set_xlabel("Day")
        ax.set_ylabel("Balance ($)")
        ax.set_title("Backtest Balance Over Time")
        st.pyplot(fig)

        st.subheader("🧾 Backtest Trade Log")
        st.dataframe(log_df, use_container_width=True)

        csv_log = log_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Trade Log CSV", csv_log, "backtest_trades.csv", "text/csv")
    else:
        st.error("❌ Failed to process CSV")
