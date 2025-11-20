# pages/View_Ticket.py
import streamlit as st
from db import (
    init_db,
    get_ticket,
    update_ticket_status,
    update_ticket,
    delete_ticket,
    list_users,
)

# -------------------------------------------------
# Config / constants
# -------------------------------------------------
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

TICKET_TYPES = [
    "Bug",
    "Test Case",
]

st.set_page_config(page_title="View Ticket", page_icon="🔍", layout="wide")
init_db()

# -------------------------------------------------
# Auth + role helpers
# -------------------------------------------------
user = st.session_state.get("user")
if not user:
    st.switch_page("pages/Login.py")

username = user["username"]
role = (user.get("role") or "").strip().lower()
is_admin = role == "admin"

# Hide Login in sidebar
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] li a[href*="Login"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Get current ticket
# -------------------------------------------------
tid = st.session_state.get("view_ticket_id")
if not tid:
    st.error("No ticket selected.")
    st.page_link("pages/Tickets.py", label="⬅ Back to Tickets")
    st.stop()

t = get_ticket(tid)
if not t:
    st.error(f"Ticket #{tid} not found.")
    st.page_link("pages/Tickets.py", label="⬅ Back to Tickets")
    st.stop()

ticket_type = t["ticket_type"]
subject = t["subject"]

# ----- ownership / permissions -----
created_by = (t["created_by"] or "").lower()
assigned_to_name = (t["assigned_to"] or "").lower() if "assigned_to" in t.keys() else ""
assigned_to_id = t["user_id"]

current_username = username.lower()
current_user_id = user.get("id")

is_creator = created_by == current_username
is_assigned = (
    assigned_to_name == current_username
    or (assigned_to_id is not None and assigned_to_id == current_user_id)
)

can_edit = is_admin or is_creator or is_assigned

st.title(f"[{ticket_type}] Ticket #{tid}")
st.caption(f"Created by {t['created_by'] or '—'} on {t['created_at']}")

# -------------------------------------------------
# Edit mode toggle
# -------------------------------------------------
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# If user isn't allowed to edit, force view-only
if not can_edit and st.session_state.edit_mode:
    st.session_state.edit_mode = False

top_c1, top_c2, top_c3 = st.columns([2, 1, 1])

with top_c1:
    st.subheader(subject)

with top_c2:
    if can_edit:
        if st.session_state.edit_mode:
            if st.button("🔒 View only", use_container_width=True):
                st.session_state.edit_mode = False
                st.rerun()
        else:
            if st.button("✏️ Edit ticket", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
    else:
        st.caption("You can view this ticket but not edit it.")

with top_c3:
    if st.button("⬅ Back to Tickets", use_container_width=True):
        st.switch_page("pages/Tickets.py")

st.divider()

# -------------------------------------------------
# Status update
# -------------------------------------------------
current_status = t["status"] or "New"
try:
    status_idx = STATUS_CHOICES.index(current_status)
except ValueError:
    status_idx = 0

cs1, cs2 = st.columns([1, 3])
with cs1:
    if can_edit:
        new_status = st.selectbox(
            "Status",
            STATUS_CHOICES,
            index=status_idx,
            key=f"detail_status_{tid}",
        )
    else:
        st.markdown("**Status**")
        st.write(current_status)
        new_status = current_status

with cs2:
    if can_edit:
        if st.button("💾 Save Status"):
            update_ticket_status(tid, new_status)
            st.success("Status updated.")
            st.rerun()
    else:
        st.caption("Only the creator, assignee, or an admin can change the status.")

st.divider()

# -------------------------------------------------
# EDIT MODE: full form to update ticket
# -------------------------------------------------
if st.session_state.edit_mode and can_edit:
    st.subheader("Edit ticket")

    # Users for assignee dropdown
    users = list_users()
    user_names = ["— Unassigned —"] + [u["username"] for u in users]
    user_ids = [None] + [u["id"] for u in users]

    # Current assignee -> dropdown index
    current_assignee_id = t["user_id"]
    if current_assignee_id in user_ids:
        current_assignee_index = user_ids.index(current_assignee_id)
    else:
        current_assignee_index = 0

    with st.form("edit_ticket", clear_on_submit=False):
        # Ticket type
        et_ticket_type = st.selectbox(
            "Ticket type",
            TICKET_TYPES,
            index=TICKET_TYPES.index(ticket_type) if ticket_type in TICKET_TYPES else 0,
        )

        et_subject = st.text_input("Subject", value=t["subject"] or "")

        if et_ticket_type == "Test Case":
            # Test Case: only need these four; summary/outcome not needed
            et_prereq = st.text_area(
                "Preconditions / Requirements",
                value=t["prerequisites"] or "",
                height=160,
            )
            et_steps = st.text_area(
                "Test Steps",
                value=t["steps_to_replicate"] or "",
                height=200,
            )
            et_expected = st.text_area(
                "Pass Criteria",
                value=t["expected_outcome"] or "",
                height=100,
            )
            # summary/outcome fields are not shown for Test Case
            et_summary = None
            et_outcome = None
        else:
            # Bug: original fields
            et_summary = st.text_input(
                "Summary",
                value=t["summary"] or "",
            )
            et_prereq = st.text_area(
                "Prerequisites",
                value=t["prerequisites"] or "",
                height=160,
            )
            et_steps = st.text_area(
                "Steps to replicate",
                value=t["steps_to_replicate"] or "",
                height=200,
            )
            et_outcome = st.text_area(
                "Outcome",
                value=t["outcome"] or "",
                height=100,
            )
            et_expected = st.text_area(
                "Expected Outcome",
                value=t["expected_outcome"] or "",
                height=100,
            )

        et_assigned_to = st.selectbox(
            "Assign to user (optional)",
            user_names,
            index=current_assignee_index,
        )
        et_user_id = user_ids[user_names.index(et_assigned_to)]

        et_parent = st.text_input(
            "Parent ticket ID (optional)",
            value=str(t["parent_id"] or ""),
        )
        et_parent_id = int(et_parent) if et_parent.strip().isdigit() else None

        save_col, cancel_col = st.columns([1, 1])
        with save_col:
            save_changes = st.form_submit_button("✅ Save changes", use_container_width=True)
        with cancel_col:
            cancel_edit = st.form_submit_button("❌ Cancel edit", use_container_width=True)

    if cancel_edit:
        st.session_state.edit_mode = False
        st.rerun()

    if save_changes:
        if not can_edit:
            st.error("You do not have permission to edit this ticket.")
            st.stop()

        # Basic validation
        errors = []
        if not et_subject.strip():
            errors.append("Subject is required.")
        if et_ticket_type == "Bug" and not (et_summary or "").strip():
            errors.append("Summary is required for Bug tickets.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # For Test Case tickets, summary & outcome are not needed → store as ""
            if et_ticket_type == "Test Case":
                summary_val = ""
                outcome_val = ""
            else:
                summary_val = (et_summary or "").strip()
                outcome_val = (et_outcome or "").strip()

            update_ticket(
                ticket_id=tid,
                ticket_type=et_ticket_type,
                subject=et_subject.strip(),
                summary=summary_val,
                prerequisites=(et_prereq or "").strip(),
                steps_to_replicate=(et_steps or "").strip(),
                outcome=outcome_val,
                expected_outcome=(et_expected or "").strip(),
                status=new_status,  # keep current status selection
                user_id=et_user_id,
                parent_id=et_parent_id,
            )
            st.success("Ticket updated successfully.")
            st.session_state.edit_mode = False
            st.rerun()

# -------------------------------------------------
# VIEW MODE (read-only details)
# -------------------------------------------------
else:
    st.subheader("Ticket details")

    if ticket_type == "Test Case":
        st.markdown("**Subject**")
        st.write(t["subject"] or "—")

        st.markdown("**Preconditions / Requirements**")
        st.write(t["prerequisites"] or "—")

        st.markdown("**Test Steps**")
        st.write(t["steps_to_replicate"] or "—")

        st.markdown("**Pass Criteria**")
        st.write(t["expected_outcome"] or "—")
    else:  # Bug
        st.markdown("**Summary**")
        st.write(t["summary"] or "—")

        st.markdown("**Prerequisites**")
        st.write(t["prerequisites"] or "—")

        st.markdown("**Steps to replicate**")
        st.write(t["steps_to_replicate"] or "—")

        st.markdown("**Outcome**")
        st.write(t["outcome"] or "—")

        st.markdown("**Expected Outcome**")
        st.write(t["expected_outcome"] or "—")

    if t["parent_id"]:
        st.markdown(f"**Parent Ticket:** #{t['parent_id']}")

    if t["user_id"]:
        st.markdown(f"**Assigned User ID:** {t['user_id']}")

# -------------------------------------------------
# Admin-only Delete
# -------------------------------------------------
st.divider()
if is_admin:
    st.error("⚠ Admin only: delete this ticket. This cannot be undone.")
    col_del1, col_del2 = st.columns([1, 3])
    with col_del1:
        if st.button("🗑️ Delete ticket", use_container_width=True):
            st.session_state.confirm_delete = True

    if st.session_state.get("confirm_delete"):
        st.warning("Are you sure you want to permanently delete this ticket?")
        cd1, cd2 = st.columns(2)
        with cd1:
            if st.button("✅ Yes, delete it"):
                delete_ticket(tid)
                st.success(f"Ticket #{tid} deleted.")
                st.session_state.pop("view_ticket_id", None)
                st.session_state.confirm_delete = False
                st.switch_page("pages/Tickets.py")
        with cd2:
            if st.button("❌ Cancel delete"):
                st.session_state.confirm_delete = False
                st.rerun()
else:
    st.caption("You do not have permission to delete this ticket.")