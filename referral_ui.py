import streamlit as st
import json
import uuid
import os
import pandas as pd
from datetime import datetime

# ------------------------------------------
# 🔧 CONFIG
REFERRAL_REWARD = 5  # USD per referral
# ------------------------------------------

# Load users from JSON
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

# Save users to JSON
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

# Generate unique referral code
def generate_referral_code():
    return str(uuid.uuid4())[:8]

# Count number of people referred by code
def get_referral_count(users, referral_code):
    return sum(1 for u in users.values() if u.get("referred_by") == referral_code)

# ------------------------------------------
# 🚀 Streamlit App Starts Here
st.set_page_config(page_title="TrustMe AI Referral Signup", layout="centered")
st.title("🚀 TrustMe AI Referral Signup")

users = load_users()

# Get referral code from URL
query_params = st.query_params
referred_by = query_params.get("ref", [None])[0]

# ------------------------------------------
# 📝 Registration Form
with st.form("registration_form"):
    name = st.text_input("👤 Your Name")
    email = st.text_input("📧 Your Email")
    submitted = st.form_submit_button("✅ Register")

if submitted:
    if email in users:
        st.warning("⚠️ You are already registered.")
    else:
        referral_code = generate_referral_code()
        users[email] = {
            "name": name,
            "email": email,
            "referral_code": referral_code,
            "referred_by": referred_by,
            "joined_at": datetime.utcnow().isoformat()
        }
        save_users(users)
        st.success("🎉 Successfully registered!")

        st.session_state["registered"] = True
        st.session_state["user_email"] = email

# ------------------------------------------
# 🔐 Referral Dashboard Section
if st.session_state.get("registered"):
    email = st.session_state["user_email"]
    user = users.get(email)

    if user:
        referral_code = user["referral_code"]
        referral_link = f"https://trustmeai.online/?ref={referral_code}"
        referral_count = get_referral_count(users, referral_code)
        earnings = referral_count * REFERRAL_REWARD

        st.markdown("---")
        st.subheader("🎁 Your Referral Dashboard")

        st.write("🔗 **Your Referral Link:**")
        st.code(referral_link)

        st.write(f"👥 **People You've Referred:** `{referral_count}`")
        st.write(f"💸 **Total Earned from Referrals:** `${earnings}`")

        # Table of referred users
        referred_users = [
            {
                "Name": u["name"],
                "Email": u["email"],
                "Earnings": f"${REFERRAL_REWARD}"
            }
            for u in users.values()
            if u.get("referred_by") == referral_code
        ]

        if referred_users:
            st.markdown("### 🧾 Referral List")
            df = pd.DataFrame(referred_users)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No one has signed up with your link yet.")

        st.write("🌱 **Referral Tree:** *(Coming soon in Phase 2)*")

# ------------------------------------------
# 📊 TrustMe AI Core Dashboard (Basic Preview)
st.markdown("---")
st.header("📊 TrustMe AI Dashboard")

if st.session_state.get("registered"):
    user = users.get(st.session_state["user_email"])
    st.success(f"Welcome, {user['name']}! 🎉")

    st.write("🧾 **Your Referral Code:**", user["referral_code"])
    st.write("🧍‍♂️ **Referred By:**", user["referred_by"] or "None")
    st.write("📅 **Joined On:**", user["joined_at"].split("T")[0])
else:
    st.warning("⚠️ Please register or login via referral page first.")
