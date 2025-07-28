
import streamlit as st

st.set_page_config(page_title="TrustMe AI Phase 2", layout="wide")

st.title("🚀 TrustMe AI - Phase 2 Dashboard")
st.markdown("Welcome to the advanced AI Trading System interface.")

with st.sidebar:
    st.header("Control Panel")
    st.slider("Daily Profit %", 0, 100, 10)
    st.slider("Reinvest Frequency (mins)", 10, 1440, 60)
    st.toggle("Auto Reinvest")

st.success("System is live. More modules coming soon!")
