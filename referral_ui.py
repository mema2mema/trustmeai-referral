import streamlit as st
import urllib.parse

st.set_page_config(page_title="TrustMe AI Referrals", layout="centered")

# Get query params
query_params = st.experimental_get_query_params()
ref_code = query_params.get("ref", [""])[0]

# Main app
st.title("🎉 Welcome to TrustMe AI")

if ref_code:
    st.success(f"You're joining with referral code: `{ref_code}`")
else:
    st.info("No referral code provided.")

# Simulate signup
with st.form("signup_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    submitted = st.form_submit_button("Sign Up")

    if submitted:
        st.success(f"Thanks for signing up, {name}!")
        your_ref_link = f"https://trustmeai.online/?ref={name[:3].lower()}123"
        st.markdown(f"🔗 Share your referral link: `{your_ref_link}`")

st.markdown("---")
st.caption("💡 TrustMe AI Referral System | Built with ❤️ by mema2mema")
