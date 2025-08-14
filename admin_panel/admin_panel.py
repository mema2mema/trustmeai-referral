import os
import pandas as pd
import streamlit as st

from db import (
    get_pending_withdrawals, update_withdrawal_status,
    adjust_user_balance, find_user, log_action,
    get_audit_logs, list_users, set_user_role, list_withdrawals, ensure_user
)

st.set_page_config(page_title="TrustMe AI — Admin", page_icon="🛡️", layout="wide")
st.title("🛡️ TrustMe AI — Admin Panel (v3.7.6)")

ADMIN_PASSPHRASE = os.getenv("ADMIN_PASSPHRASE")

if "authed" not in st.session_state:
    st.session_state.authed = False
if not st.session_state.authed:
    with st.form("auth"):
        pw = st.text_input("Enter Admin Passphrase", type="password")
        admin_display = st.text_input("Your display name (for logs)", help="E.g. @mahesh or Mahesh")
        submit = st.form_submit_button("Unlock")
    if submit:
        if ADMIN_PASSPHRASE and pw == ADMIN_PASSPHRASE:
            st.session_state.authed = True
            st.session_state.admin_display = admin_display or "admin"
            st.success("Admin unlocked ✔")
        else:
            st.error("Invalid passphrase")
    st.stop()
else:
    st.caption(f"Signed in as **{st.session_state.admin_display}**")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💸 Withdrawals", "💼 Balances", "👥 Users", "🧾 Logs", "🔧 All Withdrawals"])

with tab1:
    st.subheader("Approve / Deny Withdrawals")
    pending = get_pending_withdrawals()
    if not pending:
        st.info("No pending withdrawals.")
    else:
        df = pd.DataFrame(pending)
        st.dataframe(df, use_container_width=True)
        for row in pending:
            with st.expander(f"Request #{row['id']} — {row['amount']} by @{row.get('username') or row.get('tg_user_id')}"):
                col1, col2, col3 = st.columns(3)
                txid = col1.text_input(f"TXID for #{row['id']}", key=f"txid_{row['id']}")
                note = col2.text_input(f"Note for #{row['id']}", key=f"note_{row['id']}")
                colA, colB = st.columns(2)
                if colA.button("✅ Approve", key=f"approve_{row['id']}"):
                    updated = update_withdrawal_status(row['id'], "approved", st.session_state.admin_display, txid, note)
                    log_action(st.session_state.admin_display, "withdrawal_approve", "withdrawal", str(row['id']), {"before": row, "after": updated})
                    st.success(f"Approved withdrawal #{row['id']}")
                    st.rerun()
                if colB.button("⛔ Deny", key=f"deny_{row['id']}"):
                    updated = update_withdrawal_status(row['id'], "denied", st.session_state.admin_display, None, note or "Denied")
                    log_action(st.session_state.admin_display, "withdrawal_deny", "withdrawal", str(row['id']), {"before": row, "after": updated})
                    st.warning(f"Denied withdrawal #{row['id']}")
                    st.rerun()

with tab2:
    st.subheader("Adjust User Balances")
    ident = st.text_input("User identifier (Telegram id or @username)")
    mode = st.selectbox("Mode", ["get", "set", "add", "sub"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01, value=0.0, help="Ignored for 'get'")
    if st.button("Execute"):
        user = find_user(ident) if ident else None
        if not user:
            st.error("User not found")
        else:
            if mode == "get":
                st.info(f"Current balance for @{user.get('username') or user.get('tg_user_id')}: **{user['balance']}**")
            else:
                before = user.copy()
                updated = adjust_user_balance(user['id'], mode, amount)
                log_action(st.session_state.admin_display, f"balance_{mode}", "user", str(user['id']), {"before": before, "after": updated, "amount": amount})
                st.success(f"Balance updated: now **{updated['balance']}**")

with tab3:
    st.subheader("Users & Roles")
    users = list_users(limit=500)
    dfu = pd.DataFrame(users)
    st.dataframe(dfu, use_container_width=True)
    target = st.text_input("Change role for (Telegram id or @username)")
    new_role = st.selectbox("New role", ["admin","manager","support","user"])
    if st.button("Update Role"):
        user = find_user(target) if target else None
        if not user:
            st.error("User not found")
        else:
            before = user.copy()
            updated = set_user_role(user['id'], new_role)
            log_action(st.session_state.admin_display, "role_set", "user", str(user['id']), {"before": before, "after": updated})
            st.success(f"Role updated for @{updated.get('username') or updated.get('tg_user_id')} → **{updated['role']}**")

with tab4:
    st.subheader("Audit Logs (latest 200)")
    logs = get_audit_logs(200)
    dfl = pd.DataFrame(logs)
    st.dataframe(dfl, use_container_width=True)

with tab5:
    st.subheader("All Withdrawals")
    status = st.selectbox("Filter status", ["", "pending","approved","denied"])
    rows = list_withdrawals(status or None, limit=500)
    dfw = pd.DataFrame(rows)
    st.dataframe(dfw, use_container_width=True)
