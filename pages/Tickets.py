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
            default=["New", "Open", "In Progress"],
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

    rows = list_tickets(statuses=f_status, search=f_search)
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
    st.title("📝 Create New Ticket")

    # Users for assignee dropdown
    users = list_users()
    user_names = ["— Unassigned —"] + [u["username"] for u in users]
    user_ids = [None] + [u["id"] for u in users]

    # ticket type picker
    ticket_type = st.selectbox("Ticket type", TICKET_TYPES, index=0)

    # highlight only mandatory fields when empty (for Bug; still fine for Test Case)
    st.markdown(
        """
        <style>
        [data-testid="stTextInput"] input[aria-label="Subject"]:placeholder-shown,
        [data-testid="stTextInput"] input[aria-label="Summary"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Prerequisites"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Steps to replicate"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Outcome"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Expected Outcome"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Preconditions / Requirements"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Test Steps"]:placeholder-shown,
        [data-testid="stTextArea"] textarea[aria-label="Pass Criteria"]:placeholder-shown {
            border: 2px solid #FFD700 !important;
            border-radius: 8px !important;
            background-color: rgba(255, 215, 0, 0.03) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialise variables so they're always defined
    subject = ""
    summary = ""
    prerequisites = ""
    steps_to_replicate = ""
    outcome = ""
    expected_outcome = ""

    with st.form("new_ticket", clear_on_submit=True):

        if ticket_type == "Test Case":
            # --- Test Case form (only the 4 required fields) ---
            subject = st.text_input(
                "Subject",
                placeholder="Verify that users are only able to approve..."
            )
            prerequisites = st.text_area(
                "Preconditions / Requirements",
                height=200,
                placeholder="Environment, data, configuration required before executing the test."
            )
            steps_to_replicate = st.text_area(
                "Test Steps",
                height=260,
                placeholder="1. Step one\n2. Step two\n3. Step three"
            )
            expected_outcome = st.text_area(
                "Pass Criteria",
                height=100,
                placeholder="Verify that ..."
            )

            # summary & outcome are not used for Test Case
            summary = ""   # keeps DB happy (NOT NULL column)
            outcome = ""   # can be empty

        else:
            # --- Bug form (your original) ---
            subject = st.text_input("Subject", placeholder="Short, descriptive title")
            summary = st.text_input("Summary", placeholder="Brief summary of the issue/feature")
            prerequisites = st.text_area(
                "Prerequisites",
                height=180,
                placeholder="Required setup, Records or Settings\n1.\n2.\n3.",
            )
            steps_to_replicate = st.text_area(
                "Steps to replicate",
                height=240,
                placeholder="1. Step one\n2. Step two\n3. Step three",
            )
            outcome = st.text_area("Outcome", height=80, placeholder="What actually happened")
            expected_outcome = st.text_area(
                "Expected Outcome", height=80, placeholder="What should have happened"
            )

        assigned_to = st.selectbox("Assign to user (optional)", user_names, index=0)
        assigned_user_id = user_ids[user_names.index(assigned_to)]

        parent_input = st.text_input("Parent ticket ID (optional)", placeholder="e.g., 42")
        parent_id = int(parent_input) if parent_input.strip().isdigit() else None

        created_by = (st.session_state.get("user") or {}).get("username", "demo")

        c1, c2 = st.columns([1, 1])
        with c1:
            submitted = st.form_submit_button("✅ Create Ticket", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

    if cancel:
        st.session_state.show_form = False
        st.rerun()

    if submitted:
        # Validate required fields depending on ticket type
        if ticket_type == "Test Case":
            required_map = {
                "Subject": subject,
                "Preconditions / Requirements": prerequisites,
                "Test Steps": steps_to_replicate,
                "Pass Criteria": expected_outcome,
            }
        else:  # Bug
            required_map = {
                "Subject": subject,
                "Summary": summary,
                "Prerequisites": prerequisites,
                "Steps to replicate": steps_to_replicate,
                "Outcome": outcome,
                "Expected Outcome": expected_outcome,
            }

        missing = [name for name, val in required_map.items() if not val.strip()]

        if missing:
            st.error("Please fill in: " + ", ".join(missing))
        else:
            # Always set status to "New" on creation
            new_id = create_ticket(
                ticket_type=ticket_type,
                subject=subject.strip(),
                summary=summary.strip(),
                prerequisites=prerequisites.strip(),
                steps_to_replicate=steps_to_replicate.strip(),
                outcome=outcome.strip(),
                expected_outcome=expected_outcome.strip(),
                created_by=created_by,
                user_id=assigned_user_id,
                parent_id=parent_id,
                status="New",
            )

            st.success(f"{ticket_type} #{new_id} created successfully.")
            st.session_state.show_form = False
            st.rerun()