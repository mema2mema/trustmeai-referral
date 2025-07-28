import streamlit as st
import uuid
import pyperclip

# Simulated DB — this will be replaced with real DB logic later
mock_referrals = {
    'user123': {
        'total_referrals': 5,
        'active_referrals': 3,
        'earnings': 42.75
    }
}

def get_current_user_id():
    # Temporary static user ID
    return 'user123'

def generate_referral_link(user_id, base_url="https://trustmeai.online"):
    return f"{base_url}/?ref={user_id}"

def referral_ui():
    st.header("🤝 Invite & Earn - TrustMe AI Referral Program")
    
    user_id = get_current_user_id()
    referral_link = generate_referral_link(user_id)

    st.subheader("🔗 Your Referral Link")
    st.code(referral_link, language='text')
    if st.button("📋 Copy to Clipboard"):
        pyperclip.copy(referral_link)
        st.success("Copied to clipboard!")

    st.divider()

    st.subheader("📈 Your Referral Stats")
    stats = mock_referrals.get(user_id, {'total_referrals': 0, 'active_referrals': 0, 'earnings': 0.00})
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Referred", stats['total_referrals'])
    col2.metric("✅ Active Users", stats['active_referrals'])
    col3.metric("💵 Earnings", f"${stats['earnings']:.2f}")

    st.divider()

    st.subheader("💸 Commission Structure")
    st.markdown("""
    - 🥇 **Level 1:** 10% of referred user's deposit  
    - 🥈 **Level 2:** 5% from their referrals  
    - 🥉 **Level 3:** 2% from second-level referrals
    """)

    st.divider()

    st.subheader("📤 Invite Friends Directly")
    email = st.text_input("Enter your friend's email")
    if st.button("Send Invite"):
        if email:
            st.success(f"Invitation sent to {email} with your referral link!")
        else:
            st.error("Please enter an email address.")
