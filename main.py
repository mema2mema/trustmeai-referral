import streamlit as st
import json
from config import config
from referral_ui import load_users, get_referral_count

# Load users
users = load_users()

# Simulate user login (from session or fallback)
email = st.session_state.get("user_email", None)

st.set_page_config(page_title="TrustMe AI Dashboard", layout="centered")
st.title("📊 TrustMe AI Dashboard")

if not email or email not in users:
    st.warning("⚠️ Please register or login via referral page first.")
    st.stop()

# Get current user
user = users[email]
name = user["name"]
referral_code = user["referral_code"]
referral_count = get_referral_count(users, referral_code)
referral_link = f"https://trustmeai.online/?ref={referral_code}"
referral_reward = referral_count * 5

# ------------------- Investment Panel -------------------
st.subheader("💼 Investment Overview")

st.write("👤 Name:", name)
st.write("📧 Email:", email)
st.write("💰 Initial Investment:", f"${config['initial_investment']}")
st.write("📈 Daily Profit %:", f"{config['daily_profit_percent']}%")
st.write("📅 Duration:", f"{config['days']} days")
st.write("🔁 Mode:", config["mode"].capitalize())

# Placeholder for profit calculation (you can enhance later)
estimated_profit = config['initial_investment']
for day in range(config["days"]):
    profit_today = estimated_profit * (config["daily_profit_percent"] / 100)
    if config["mode"] == "reinvest":
        estimated_profit += profit_today
    else:
        pass  # withdraw mode can skip reinvest logic

st.write("💵 Estimated Final Profit:", f"${int(estimated_profit):,}")

# ------------------- Referral Panel -------------------
st.markdown("---")
st.subheader("🎁 Your Referral Stats")

st.write("🔗 **Referral Link:**")
st.code(referral_link)

st.write(f"👥 **People You've Referred:** `{referral_count}`")
st.write(f"💰 **Total Earned from Referrals:** `${referral_reward}`")

# Table of referred users
referred_users = [
    {"Name": u["name"], "Email": u["email"]}
    for u in users.values()
    if u.get("referred_by") == referral_code
]

if referred_users:
    st.markdown("### 🧾 People You've Referred")
    st.dataframe(referred_users, use_container_width=True)
else:
    st.info("No referrals yet. Share your link to start earning!")
