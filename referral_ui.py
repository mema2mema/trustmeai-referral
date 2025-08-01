import json
import os
import streamlit as st
import pyperclip

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user(user_id):
    users = load_users()
    for user in users:
        if user["user_id"] == user_id:
            return user
    return None

def register_user(user_id, referred_by=None):
    users = load_users()
    if get_user(user_id):
        return
    new_user = {
        "user_id": user_id,
        "referred_by": referred_by,
        "referrals": [],
        "earnings": 0.0
    }
    users.append(new_user)
    if referred_by:
        ref_user = get_user(referred_by)
        if ref_user:
            ref_user["referrals"].append(user_id)
    save_users(users)

def get_referral_count(user_id):
    user = get_user(user_id)
    if not user:
        return 0
    return len(user["referrals"])

def show_referral_ui(current_user):
    st.subheader("🔗 Referral Program")
    link = f"http://localhost:8501/?ref={current_user}"
    st.text_input("Your Referral Link", link)
    if st.button("Copy Link"):
        pyperclip.copy(link)
        st.success("Link copied to clipboard!")

    count = get_referral_count(current_user)
    st.info(f"👥 You referred {count} user(s).")