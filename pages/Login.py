import streamlit as st
from db import init_db
from auth import verify_user
from sidebar import is_logged_in, hide_other_pages_on_login

st.set_page_config(page_title="Sign in", page_icon="🔐", layout="centered")
init_db()

# If already logged in, do NOT show login page; send to Home
if is_logged_in():
    st.switch_page("Home.py")

# Hide other pages in sidebar while on login
hide_other_pages_on_login()

st.title("🔐 Sign in to TicketApp")

with st.form("login", clear_on_submit=False):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign in", use_container_width=True)

if submitted:
    if not username.strip() or not password:
        st.warning("Please enter both username and password.")
    else:
        user = verify_user(username.strip(), password)
        if user:
            st.session_state.user = user
            st.success(f"Welcome, {user['username']}!")
            st.switch_page("Home.py")
        else:
            st.error("Invalid username or password.")