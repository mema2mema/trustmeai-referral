import streamlit as st
import json
import uuid
import os
import pandas as pd
from datetime import datetime

# Load users
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

# Save users
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

# Generate referral code
def generate_referral_code():
    return str(uuid.uuid4())[:8]

# Count referrals
def get_referral_count(users, code):
    return sum(1 for u in users.values() if u.get("referred_by") == code)

# Streamlit UI
st.title("🚀 TrustMe AI Referral Signup")

users = load_users()

# Get ?ref= code from URL
query_params = st.query_params
referred_by = query_params.get("ref", [None])[0]

# Registration form
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

# Show referral info
if st.session_state.get("registered"):
    email = st.session_state["user_email"]
    user = users.get(email)

    if user:
        st.markdown("---")
        st.subheader("🎁 Your Referral Dashboard")

        referral_code = user["referral_code"]
        referral_link = f"https://trustmeai.online/?ref={referral_code}"
        referral_count = get_referral_count(users, referral_code)

        st.write("🔗 **Your Referral Link:**")
        st.code(referral_link)

        st.write(f"👥 **People You've Referred:** `{referral_count}`")

        referred_users = [
            {
                "Name": u["name"],
                "Email": u["email"]
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

        st.write("🌱 **Referral Tree:** *(Coming soon)*")
