import streamlit as st
from datetime import datetime, timedelta

from db import (
    init_db,
    list_tickets,
)

# -------------------------------------------------
# Page + DB init
# -------------------------------------------------
st.set_page_config(page_title="TicketApp - Home", page_icon="🎫", layout="wide")
init_db()

# -------------------------------------------------
# Auth gate
# -------------------------------------------------
user = st.session_state.get("user")

if not user:
    # Not signed in → go to Login
    st.switch_page("pages/Login.py")

# Hide Login page link in sidebar when logged in
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] li a[href*="Login"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

username = user["username"]

# -------------------------------------------------
# Load ticket data
# -------------------------------------------------
# list_tickets(None, "") → all tickets
rows = list_tickets(statuses=None, search="")

# rows is a list of sqlite3.Row
tickets = list(rows)

# Helper to parse created_at safely
def parse_created_at(value):
    if not value:
        return None
    try:
        # SQLite datetime('now') → "YYYY-MM-DD HH:MM:SS"
        return datetime.fromisoformat(value)
    except Exception:
        return None

now = datetime.utcnow()
week_ago = now - timedelta(days=7)

total_tickets = len(tickets)

# Status buckets
OPEN_STATUSES = {
    "New",
    "Open",
    "In Progress",
    "Test: Sprint Test",
    "Test: Build Ready",
    "Test: Regression",
    "Product Backlog - Pending (B)",
}

open_tickets = [t for t in tickets if (t["status"] in OPEN_STATUSES)]
new_this_week = [
    t for t in tickets
    if (dt := parse_created_at(t["created_at"])) is not None and dt >= week_ago
]

# Tickets assigned to the logged-in user
assigned_to_me = [
    t for t in tickets
    if (t["assigned_to"] or "").lower() == username.lower()
]

# Status counts for small table
status_counts = {}
for t in tickets:
    status_counts[t["status"]] = status_counts.get(t["status"], 0) + 1


# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("🏠 TicketApp Home")
st.caption(f"Signed in as **{username}**")

st.markdown("---")

# Top metrics row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total tickets", total_tickets)
with c2:
    st.metric("Open tickets", len(open_tickets))
with c3:
    st.metric("New in last 7 days", len(new_this_week))
with c4:
    st.metric("Assigned to you", len(assigned_to_me))

st.markdown("---")

# Two columns layout: status breakdown + assigned to me
left, right = st.columns([1, 1.2])

with left:
    st.subheader("📊 Status breakdown")

    if not status_counts:
        st.info("No tickets in the system yet.")
    else:
        # simple table of status counts
        for status, count in sorted(status_counts.items()):
            st.write(f"- **{status}**: {count}")

with right:
    st.subheader("🧾 Tickets assigned to you")

    if not assigned_to_me:
        st.info("You currently have no tickets assigned.")
    else:
        # Simple compact list with View buttons
        for t in assigned_to_me:
            tid = t["ticket_id"]
            subject = t["subject"]
            status = t["status"]
            created_at = t["created_at"]
            ticket_type = t["ticket_type"]

            row_c1, row_c2, row_c3 = st.columns([5, 2, 1])
            with row_c1:
                st.markdown(
                    f"**[{ticket_type}] #{tid} — {subject}**  \n"
                    f"<small>Status: `{status}` • Created: {created_at}</small>",
                    unsafe_allow_html=True,
                )
            with row_c2:
                st.write("")  # spacer
            with row_c3:
                if st.button("View", key=f"home_view_{tid}"):
                    st.session_state.view_ticket_id = tid
                    st.switch_page("pages/View_Ticket.py")

            st.markdown("<hr style='margin: 0.4rem 0;'>", unsafe_allow_html=True)

# Sidebar: basic navigation + logout
with st.sidebar:
    st.success(f"Signed in as {username}")
    st.page_link("Home.py", label="Home", icon="🏠")
    st.page_link("pages/Tickets.py", label="Tickets", icon="📋")

    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()