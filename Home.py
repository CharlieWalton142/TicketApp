import streamlit as st
from datetime import datetime, timedelta
from collections import Counter
import pandas as pd

from sidebar import (
    require_login,
    hide_login_link_if_logged_in,
    hide_admin_page_for_non_admin,
    get_current_user,
    is_admin,
)

from db import init_db, list_tickets

# -------------------------------------------------
# Page + DB init
# -------------------------------------------------
st.set_page_config(page_title="TicketApp - Home", page_icon="🎫", layout="wide")
init_db()

# -------------------------------------------------
# Auth gate
# -------------------------------------------------
require_login()
hide_login_link_if_logged_in()
hide_admin_page_for_non_admin()

user = get_current_user()
username = user["username"]
admin = is_admin()

with st.sidebar:
    st.success("Use the sidebar to switch pages.")
    if user and st.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# -------------------------------------------------
# Load ticket data
# -------------------------------------------------
rows = list_tickets(statuses=None, search="")
tickets = list(rows)

def parse_created_at(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None

now = datetime.utcnow()
week_ago = now - timedelta(days=7)

total_tickets = len(tickets)

OPEN_STATUSES = {
    "New",
    "Open",
    "In Progress",
    "Test: Sprint Test",
    "Test: Build Ready",
    "Test: Regression",
    "Product Backlog - Pending (B)",
}

open_tickets = [t for t in tickets if t["status"] in OPEN_STATUSES]
new_this_week = [
    t for t in tickets
    if (dt := parse_created_at(t["created_at"])) is not None and dt >= week_ago
]

assigned_to_me = [
    t for t in tickets
    if (t["assigned_to"] or "").lower() == username.lower()
]

status_counts = Counter(t["status"] for t in tickets)
unassigned_tickets = [t for t in tickets if not t["assigned_to"]]

# -------------------------------------------------
# UI
# -------------------------------------------------
st.title("🏠 TicketApp Home")
st.caption(f"Signed in as **{username}**")
st.markdown("---")

# ---- Top metrics (boxed) ----
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total tickets", total_tickets)
    with c2:
        st.metric("Open tickets", len(open_tickets))
    with c3:
        st.metric("New in last 7 days", len(new_this_week))
    with c4:
        st.metric("Assigned to you", len(assigned_to_me))

st.markdown("")


# -------------------------------------------------
# Admin-only widgets (narrow, centered)
# -------------------------------------------------
if admin:
    st.markdown("---")
    st.subheader("🛠️ Admin system overview")

 # Center the admin section so it's not edge-to-edge
    outer_left, outer_center, outer_right = st.columns([0.05, 0.9, 0.05])

    with outer_center:
        # ---------- ROW 1 ----------
        row1_col1, row1_col2 = st.columns(2)

        # 1️⃣ System KPIs
        with row1_col1:
            with st.container(border=True):
                st.markdown("#### System KPIs")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total tickets (system)", total_tickets)
                with c2:
                    st.metric("Open / In Progress", len(open_tickets))
                with c3:
                    st.metric("Unassigned tickets", len(unassigned_tickets))

        # 2️⃣ In Progress tickets per user
        with row1_col2:
            with st.container(border=True):
                st.markdown("#### In Progress tickets per user")

                in_progress = [t for t in tickets if t["status"] == "In Progress"]
                if in_progress:
                    from collections import Counter
                    counts = Counter((t["assigned_to"] or "Unassigned") for t in in_progress)
                    df_inprog = (
                        pd.DataFrame(
                            [{"user": u, "in_progress": c} for u, c in counts.items()]
                        )
                        .sort_values("in_progress", ascending=False)
                    )
                    st.table(df_inprog)
                else:
                    st.info("No tickets are currently In Progress.")

        st.markdown("")  # small gap between rows

        # ---------- ROW 2 ----------
        row2_col1, row2_col2 = st.columns(2)

        # 3️⃣ Tickets by status
        with row2_col1:
            with st.container(border=True):
                st.markdown("#### Tickets by status")
                if tickets and status_counts:
                    df_status = (
                        pd.DataFrame(
                            [{"status": s, "count": c} for s, c in status_counts.items()]
                        )
                        .sort_values("count", ascending=False)
                        .set_index("status")
                    )
                    st.bar_chart(df_status)
                else:
                    st.info("No tickets to display.")

        # 4️⃣ Unassigned tickets
        with row2_col2:
            with st.container(border=True):
                st.markdown("#### Unassigned tickets")
                if not unassigned_tickets:
                    st.info("All tickets are assigned. ✅")
                else:
                    for t in unassigned_tickets[:10]:
                        tid = t["ticket_id"]
                        subject = t["subject"]
                        status = t["status"]
                        created_at = t["created_at"]
                        ticket_type = t["ticket_type"]

                        st.markdown(
                            f"**[{ticket_type}] #{tid} — {subject}**  \n"
                            f"*Status:* `{status}` • *Created:* {created_at} • "
                            f"*Created by:* {t['created_by'] or '—'}"
                        )
                        if st.button("View", key=f"home_view_unassigned_{tid}"):
                            st.session_state.view_ticket_id = tid
                            st.switch_page("pages/View_Ticket.py")
                        st.markdown(
                            "<hr style='margin: 0.4rem 0;'>",
                            unsafe_allow_html=True,
                        )
else:
        # ---- Status breakdown + assigned-to-me (each boxed) ----
    left, right = st.columns([1, 1.2])

    with left:
        with st.container(border=True):
            st.subheader("📊 Status breakdown")
            if not status_counts:
                st.info("No tickets in the system yet.")
            else:
                for status, count in sorted(status_counts.items()):
                    st.write(f"- **{status}**: {count}")

    with right:
        with st.container(border=True):
            st.subheader("🧾 Tickets assigned to you")

            if not assigned_to_me:
                st.info("You currently have no tickets assigned.")
            else:
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

                    st.markdown(
                        "<hr style='margin: 0.4rem 0;'>",
                        unsafe_allow_html=True,
                    )