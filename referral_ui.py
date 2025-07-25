import streamlit as st
import json
import uuid
import os
import pandas as pd
from datetime import datetime

# ---------- File Helpers ----------

def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def generate_referral_code():
    return str(uuid.uuid4())[:8]

def get_referral_count(users, code):
    return sum(1 for u in users.values() if u.get("referred_by") == code)

# ---------- App Start ----------

st.set_page_config(page_title="TrustMe AI Referral", layout="centered")
st.title("🚀 TrustMe AI Referral Signup")

users = load_users()

# ✅ Get referral code from URL
query_params = st.query_params
referred_by = query_params.get("ref", [None])[0]

# ---------- Registration Form ----------

with st.form("signup_form"):
    name = st.text_input("👤 Your Name")
    email = st.text_input("📧 Your Email")
    submitted = st.form_submit_button("✅ Sign Up")

if submitted:
    if email in users:
        st.warning("⚠️ This email is already registered.")
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
        st.success("🎉 You're successfully registered!")
        st.session_state["registered"] = True
        st.session_state["user_email"] = email

# ---------- Referral Dashboard ----------

if st.session_state.get("registered"):
    email = st.session_state["user_email"]
    user = users.get(email)

    if user:
        st.markdown("---")
        st.subheader("🎁 Your Referral Dashboard")

        my_code = user["referral_code"]
        my_link = f"https://trustmeai.online/?ref={my_code}"
        count = get_referral_count(users, my_code)

        st.write("🔗 **Your Referral Link:**")
        st.code(my_link, language="text")

        st.write(f"👥 **Referrals Count:** `{count}`")

        referred_users = [
            {"Name": u["name"], "Email": u["email"], "Joined": u["joined_at"][:10]}
            for u in users.values()
            if u.get("referred_by") == my_code
        ]

        if referred_users:
            st.markdown("### 🧾 People You Referred")
            df = pd.DataFrame(referred_users)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No one has signed up with your link yet.")

        st.markdown("🌱 **Referral Tree:** Coming soon...")

st.markdown("---")
st.caption("🔒 TrustMe AI · Built with ❤️ by mema2mema · 2025")
