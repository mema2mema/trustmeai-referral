import streamlit as st
import json
import uuid
import os

# === Load users.json ===
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as file:
            return json.load(file)
    return {}

# === Save to users.json ===
def save_users(users):
    with open("users.json", "w") as file:
        json.dump(users, file, indent=4)

# === Generate a referral code ===
def generate_referral_code():
    return str(uuid.uuid4())[:8]  # 8-character code

# === Count how many people this user referred ===
def get_referral_count(users, user_code):
    return sum(1 for u in users.values() if u.get("referred_by") == user_code)

# === Streamlit App ===
st.set_page_config(page_title="TrustMe AI Signup", page_icon="🚀")
st.title("🚀 TrustMe AI Referral Signup")

users = load_users()

# === Get ?ref=abc123 from URL ===
query_params = st.experimental_get_query_params()
referred_by = query_params.get("ref", [None])[0]

# === Registration form ===
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
        }
        save_users(users)
        st.success("🎉 Registration successful!")

        # === Show Referral Info ===
        st.markdown("---")
        st.subheader("🎁 Your Referral Details")

        referral_link = f"https://trustmeai.online/?ref={referral_code}"
        referral_count = get_referral_count(users, referral_code)

        st.write("🔗 **Your Referral Code:**")
        st.code(referral_code)

        st.write("🌐 **Your Referral Link:**")
        st.code(referral_link)

        st.write(f"👥 **People You've Referred:** `{referral_count}`")

        st.write("🌳 **Referral Tree:** *(coming soon in Phase 2)*")

        # Save session info
        st.session_state["registered"] = True
        st.session_state["user_email"] = email

# === If already registered in session, show info again ===
if st.session_state.get("registered"):
    email = st.session_state["user_email"]
    user = users.get(email)
    if user:
        st.markdown("---")
        st.subheader("🎁 Your Referral Details (Session)")

        referral_code = user["referral_code"]
        referral_link = f"https://trustmeai.online/?ref={referral_code}"
        referral_count = get_referral_count(users, referral_code)

        st.write("🔗 **Your Referral Code:**")
        st.code(referral_code)

        st.write("🌐 **Your Referral Link:**")
        st.code(referral_link)

        st.write(f"👥 **People You've Referred:** `{referral_count}`")

        st.write("🌳 **Referral Tree:** *(coming soon)*")
