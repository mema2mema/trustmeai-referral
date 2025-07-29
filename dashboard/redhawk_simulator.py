import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import json

# Allow root imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.telegram_alert import send_telegram_message

# --- Title ---
st.title("🦅 RedHawk Profit Simulator")

# --- Default Inputs ---
initial_investment = st.number_input("💵 Initial Investment", value=150)
daily_percent = st.number_input("📈 Daily Profit %", value=35)
days = st.slider("📅 Number of Days", 1, 365, value=10)
trades_per_day = st.slider("🔁 Trades per Day", 1, 100, value=5)
mode = st.selectbox("💼 RedHawk Profit Mode", ["🔁 Reinvest", "💸 Withdraw", "⚡ Withdraw Anytime"])

# --- Check Telegram Trigger ---
telegram_req_path = "logs/telegram_sim_request.json"
if os.path.exists(telegram_req_path):
    st.info("📩 Telegram simulation request detected. Auto-loading...")
    with open(telegram_req_path, "r") as f:
        req = json.load(f)
        initial_investment = req["Initial Investment"]
        daily_percent = req["Daily Profit %"]
        days = req["Days"]
        trades_per_day = req["Trades/Day"]
        mode = req["Mode"]
    os.remove(telegram_req_path)

# --- AI Risk Warning ---
if daily_percent > 150 or trades_per_day > 50:
    st.warning("⚠️ Unrealistic settings detected. Be cautious.")

# --- Initialize ---
balance = initial_investment
withdrawn = 0
log = []

# --- Simulation ---
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
                    f"🚨 <b>Manual Withdraw</b>\n📅 Day {day}, Trade {trade}\n💸 Amount: <b>${balance:.2f}</b>"
                )
                st.success(f"✅ You withdrew ${balance:.2f} at Day {day}, Trade {trade}")
                balance = 0
                log.append((day, trade, balance, withdrawn))
                break

# --- Save Outputs ---
df = pd.DataFrame(log, columns=["Day", "Trade", "Balance", "Withdrawn"])
os.makedirs("logs", exist_ok=True)
df.to_csv("logs/redhawk_trade_log.csv", index=False)

summary_text = f"""
📅 Days: {days}
💵 Initial Investment: ${initial_investment}
📈 Daily Profit %: {daily_percent}
🔁 Trades/Day: {trades_per_day}
💰 Final Balance: ${balance:.2f}
💸 Total Withdrawn: ${withdrawn:.2f}
"""
with open("logs/summary.txt", "w", encoding="utf-8") as f:
    f.write(summary_text.strip())

status_data = {
    "Initial Investment": f"${initial_investment}",
    "Daily Profit %": f"{daily_percent}%",
    "Days": days,
    "Trades/Day": trades_per_day,
    "Mode": mode.replace("💼 ", "").strip()
}
with open("logs/status.json", "w", encoding="utf-8") as f:
    json.dump(status_data, f, indent=2)

# --- Display ---
st.subheader("📈 Final Results")
st.write(f"💰 Final Balance: ${balance:.2f}")
st.write(f"💸 Total Withdrawn: ${withdrawn:.2f}")

st.subheader("📊 Growth Chart")
fig, ax = plt.subplots()
ax.plot(df["Balance"], label="Balance")
ax.plot(df["Withdrawn"], label="Withdrawn")
ax.set_xlabel("Trades")
ax.set_ylabel("Amount ($)")
ax.legend()
st.pyplot(fig)
fig.savefig("logs/redhawk_chart.png")

st.subheader("📄 Export")
st.download_button("📥 Download Trade Log CSV", df.to_csv(index=False), "redhawk_trade_log.csv")
