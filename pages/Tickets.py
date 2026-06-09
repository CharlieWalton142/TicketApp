# pages/Tickets.py
import streamlit as st
from db import (
    init_db,
    list_users,
    create_ticket,
    list_tickets,
    get_ticket,          # still used for detail in future if needed
    update_ticket_status,
)

from sidebar import require_login, hide_login_link_if_logged_in, hide_admin_page_for_non_admin, get_current_user
from ticket_form import render_create_ticket_form


# ---- Status options (for browsing/updating only) ----
STATUS_CHOICES = [
    "New",
    "Product Backlog - Pending (B)",
    "Test: Sprint Test",
    "Test: Build Ready",
    "Test: Regression",
    "Released",
    "Open",
    "In Progress",
    "Closed",
]

# ---- Ticket types ----
TICKET_TYPES = [
    "Bug",
    "Test Case",
]

# -------------------------------------------------
# Boot
# -------------------------------------------------
st.set_page_config(page_title="Tickets", page_icon="📋", layout="wide")
init_db()

# Auth and SAidebar clean up
require_login()
hide_login_link_if_logged_in()
hide_admin_page_for_non_admin()

current_user = get_current_user()

# UI state
if "show_form" not in st.session_state:
    st.session_state.show_form = False

# Auth gate + hide Login link if signed in
if not st.session_state.get("user"):
    st.switch_page("pages/Login.py")
else:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] li a[href*="Login"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

# -------------------------------------------------
# Sidebar 
# -------------------------------------------------

if not st.session_state.show_form:
    with st.sidebar:
        st.subheader("Filters")
        f_status = st.multiselect(
            "Status",
            STATUS_CHOICES,
        )
        f_ticket_type = st.selectbox(
            "Ticket type",
            ["Any"] + TICKET_TYPES,
            index=0,
        )
        f_search = st.text_input("Search", placeholder="subject, summary, expected outcome…")
        st.divider()
        if st.button("➕ New Ticket", use_container_width=True):
            st.session_state.show_form = True
            st.rerun()
else:
    with st.sidebar:
        if st.button("⬅ Back to Tickets", use_container_width=True):
            st.session_state.show_form = False
            st.rerun()

# -------------------------------------------------
# MODE 1: Browse / Search (list + View button)
# -------------------------------------------------
if not st.session_state.show_form:
    st.title("📋 Tickets")

    rows = list_tickets(
        ticket_types=None if f_ticket_type == "Any" else [f_ticket_type],
        statuses=f_status,
        search=f_search
    )
    if not rows:
        st.info("No tickets match your filters.")
    else:
        st.caption("Click ‘View’ to open a ticket in a detailed view page.")

        for row in rows:
            tid = row["ticket_id"]
            ticket_type = row["ticket_type"]
            subject = row["subject"]
            status = row["status"]
            created_by = row["created_by"]
            created_at = row["created_at"]
            assigned_to = row["assigned_to"]

            with st.container():
                c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 1])

                with c1:
                    st.markdown(
                        f"**[{ticket_type}] #{tid} — {subject}**  \n"
                        f"<small>by {created_by or '—'}</small>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(f"**Status:** `{status}`")
                with c3:
                    st.markdown(f"**Assigned:** {assigned_to or '—'}")
                with c4:
                    st.markdown(f"**Created:** {created_at}")
                with c5:
                    if st.button("View", key=f"view_{tid}"):
                        st.session_state.view_ticket_id = tid
                        st.switch_page("pages/View_Ticket.py")

                st.markdown("---")

# -------------------------------------------------
# MODE 2: Create
# -------------------------------------------------
else:
    render_create_ticket_form(TICKET_TYPES)