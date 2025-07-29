import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# Allow importing from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.telegram_alert import send_telegram_message  # Your existing function

# --- Title ---
st.title("🦅 RedHawk Profit Simulator")

# --- User Inputs ---
initial_investment = st.number_input("💵 Initial Investment", value=150)
daily_percent = st.number_input("📈 Daily Profit %", value=35)
days = st.slider("📅 Number of Days", 1, 365, value=10)
trades_per_day = st.slider("🔁 Trades per Day", 1, 100, value=5)
mode = st.selectbox("💼 RedHawk Profit Mode", ["🔁 Reinvest", "💸 Withdraw", "⚡ Withdraw Anytime"])

# --- AI Risk Warning ---
if daily_percent > 150 or trades_per_day > 50:
    st.warning("⚠️ Unrealistic settings: Daily % or trades/day are very high. Consider reducing for realism.")

# --- Initialize ---
balance = initial_investment
withdrawn = 0
log = []

# --- Simulation Loop ---
for day in range(1, days + 1):
    for trade in range(1, trades_per_day + 1):
        profit = balance * (daily_percent / trades_per_day) / 100

        if mode == "🔁 Reinvest":
            balance += profit
            log.append((day, trade, balance, withdrawn))

        elif mode == "💸 Withdraw":
            withdrawn += profit
            log.append((day, trade, balance, withdrawn))

        elif mode == "⚡ Withdraw Anytime":
            st.write(f"📊 Day {day} - Trade {trade} Profit: ${profit:.2f}")
            if st.button(f"💸 Withdraw Now After Trade {trade} (Day {day})", key=f"{day}_{trade}"):
                withdrawn += balance
                send_telegram_message(
                    f"🚨 <b>RedHawk Manual Withdraw</b>\n📅 Day {day}, Trade {trade}\n💸 Withdrawn: <b>${balance:.2f}</b>"
                )
                st.success(f"✅ You withdrew ${balance:.2f} at Day {day}, Trade {trade}")
                balance = 0
                log.append((day, trade, balance, withdrawn))
                break

# --- Convert to DataFrame ---
df = pd.DataFrame(log, columns=["Day", "Trade", "Balance", "Withdrawn"])

# --- Final Results ---
st.subheader("📈 Final Results")
st.write(f"💰 Final Balance: ${balance:.2f}")
st.write(f"💸 Total Withdrawn: ${withdrawn:.2f}")

# --- Chart ---
st.subheader("📊 Growth Chart")
fig, ax = plt.subplots()
ax.plot(df["Balance"], label="Balance")
ax.plot(df["Withdrawn"], label="Withdrawn")
ax.set_xlabel("Trades")
ax.set_ylabel("Amount ($)")
ax.legend()
st.pyplot(fig)

# --- CSV Export ---
st.subheader("📄 Export Trade Log")
csv_path = "logs/redhawk_trade_log.csv"
os.makedirs("logs", exist_ok=True)
df.to_csv(csv_path, index=False)
with open(csv_path, "rb") as f:
    st.download_button("📥 Download Trade Log CSV", f, file_name="redhawk_trade_log.csv")
