import streamlit as st
from db import init_db
from auth import verify_user

st.set_page_config(page_title="Sign in", page_icon="🔐", layout="centered")
init_db()

if st.session_state.get("user"):
    st.switch_page("Home.py")
else:
    st.markdown(""" 
        <style>
            /* hide any sidebar link whose label is 'Tickets' */
            [data-testid="stSidebarNav"] li a[href*="Tickets"] 
            {
                display: none !important;
            }
        </style> """, unsafe_allow_html=True)  

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