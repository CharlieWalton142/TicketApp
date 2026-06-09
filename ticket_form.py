import streamlit as st

from db import (
    list_users,
    create_ticket,
)

from ai_helper import generate_ticket_from_subject
from db import get_ai_ticket_examples


def inject_create_ticket_css():
    st.markdown("""
    <style>

    /* RED = mandatory fields */
    [data-testid="stTextInput"] input[aria-label="Subject"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Prerequisites"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Steps to replicate"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Outcome"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Expected Outcome"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Preconditions / Requirements"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Test Steps"]:placeholder-shown,
    [data-testid="stTextArea"] textarea[aria-label="Pass Criteria"]:placeholder-shown {
        border: 2px solid #ff4b4b !important;
        border-radius: 8px !important;
        background-color: rgba(255, 75, 75, 0.05) !important;
    }

    /* YELLOW = optional fields */
    [data-testid="stTextInput"] input[aria-label="Summary"]:placeholder-shown {
        border: 2px solid #FFD700 !important;
        border-radius: 8px !important;
        background-color: rgba(255, 215, 0, 0.03) !important;
    }

    </style>
    """, unsafe_allow_html=True)


def init_ai_state():
    defaults = {
        "create_subject": "",
        "ai_summary": "",
        "ai_prereq": "",
        "ai_steps": "",
        "ai_outcome": "",
        "ai_expected": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_ai_fields():
    st.session_state.ai_summary = ""
    st.session_state.ai_prereq = ""
    st.session_state.ai_steps = ""
    st.session_state.ai_outcome = ""
    st.session_state.ai_expected = ""


def render_subject_with_ai(ticket_type):
    subject_col, generate_col = st.columns([5, 1])

    with subject_col:
        st.text_input(
            "Subject",
            placeholder=(
                "Verify that users are only able to approve..."
                if ticket_type == "Test Case"
                else "Short, descriptive title"
            ),
            key="create_subject",
        )

    with generate_col:
        st.write("")
        st.write("")
        if st.button("✨ Generate", use_container_width=True):
            subject = st.session_state.get("create_subject", "").strip()

            if not subject:
                st.warning("Please enter a subject first.")
                return

            with st.spinner("Generating ticket fields..."):
                examples = get_ai_ticket_examples(
                    subject=subject,
                    ticket_type=ticket_type,
                )
                generated = generate_ticket_from_subject(
                    ticket_type=ticket_type,
                    subject=subject,
                    examples=examples,
                )

            st.session_state.ai_summary = generated.get("summary", "")
            st.session_state.ai_prereq = generated.get("prerequisites", "")
            st.session_state.ai_steps = generated.get("steps_to_replicate", "")
            st.session_state.ai_outcome = generated.get("outcome", "")
            st.session_state.ai_expected = generated.get("expected_outcome", "")

            st.success("AI draft generated. You can edit it before saving.")
            st.rerun()


def render_ticket_fields(ticket_type):
    """
    Renders the correct fields and returns a dict containing form values.
    Subject is handled outside the form so the Generate button can work.
    """
    subject = st.session_state.get("create_subject", "")

    with st.form("new_ticket", clear_on_submit=False):
        if ticket_type == "Test Case":
            prerequisites = st.text_area(
                "Preconditions / Requirements",
                value=st.session_state.ai_prereq,
                height=200,
                placeholder="Environment, data, configuration required before executing the test.",
            )
            steps_to_replicate = st.text_area(
                "Test Steps",
                value=st.session_state.ai_steps,
                height=260,
                placeholder="1. Step one\n2. Step two\n3. Step three",
            )
            expected_outcome = st.text_area(
                "Pass Criteria",
                value=st.session_state.ai_expected,
                height=100,
                placeholder="Verify that ...",
            )

            summary = ""
            outcome = ""

        else:
            summary = st.text_input(
                "Summary",
                value=st.session_state.ai_summary,
                placeholder="Brief summary of the issue/feature",
            )
            prerequisites = st.text_area(
                "Prerequisites",
                value=st.session_state.ai_prereq,
                height=180,
                placeholder="Required setup, Records or Settings\n1.\n2.\n3.",
            )
            steps_to_replicate = st.text_area(
                "Steps to replicate",
                value=st.session_state.ai_steps,
                height=240,
                placeholder="1. Step one\n2. Step two\n3. Step three",
            )
            outcome = st.text_area(
                "Outcome",
                value=st.session_state.ai_outcome,
                height=80,
                placeholder="What actually happened",
            )
            expected_outcome = st.text_area(
                "Expected Outcome",
                value=st.session_state.ai_expected,
                height=80,
                placeholder="What should have happened",
            )

        users = list_users()
        user_names = ["— Unassigned —"] + [u["username"] for u in users]
        user_ids = [None] + [u["id"] for u in users]

        assigned_to = st.selectbox("Assign to user (optional)", user_names, index=0)
        assigned_user_id = user_ids[user_names.index(assigned_to)]

        parent_input = st.text_input("Parent ticket ID (optional)", placeholder="e.g., 42")
        parent_id = int(parent_input) if parent_input.strip().isdigit() else None

        c1, c2 = st.columns([1, 1])
        with c1:
            submitted = st.form_submit_button("✅ Create Ticket", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

    return {
        "subject": subject,
        "summary": summary,
        "prerequisites": prerequisites,
        "steps_to_replicate": steps_to_replicate,
        "outcome": outcome,
        "expected_outcome": expected_outcome,
        "assigned_user_id": assigned_user_id,
        "parent_id": parent_id,
        "submitted": submitted,
        "cancel": cancel,
    }


def validate_ticket(ticket_type, values):
    if ticket_type == "Test Case":
        required_map = {
            "Subject": values["subject"],
            "Preconditions / Requirements": values["prerequisites"],
            "Test Steps": values["steps_to_replicate"],
            "Pass Criteria": values["expected_outcome"],
        }
    else:
        required_map = {
            "Subject": values["subject"],
            "Prerequisites": values["prerequisites"],
            "Steps to replicate": values["steps_to_replicate"],
            "Outcome": values["outcome"],
            "Expected Outcome": values["expected_outcome"],
        }

    return [name for name, val in required_map.items() if not val.strip()]


def save_ticket(ticket_type, values):
    created_by = (st.session_state.get("user") or {}).get("username", "demo")

    return create_ticket(
        ticket_type=ticket_type,
        subject=values["subject"].strip(),
        summary=values["summary"].strip(),
        prerequisites=values["prerequisites"].strip(),
        steps_to_replicate=values["steps_to_replicate"].strip(),
        outcome=values["outcome"].strip(),
        expected_outcome=values["expected_outcome"].strip(),
        created_by=created_by,
        user_id=values["assigned_user_id"],
        parent_id=values["parent_id"],
        status="New",
    )


def render_create_ticket_form(ticket_types):
    st.title("📝 Create New Ticket")

    inject_create_ticket_css()
    init_ai_state()

    ticket_type = st.selectbox("Ticket type", ticket_types, index=0)

    # If user changes type, clear old AI fields so Bug/Test Case values don't bleed across
    if st.session_state.get("last_ticket_type") != ticket_type:
        clear_ai_fields()
        st.session_state.last_ticket_type = ticket_type

    render_subject_with_ai(ticket_type)

    values = render_ticket_fields(ticket_type)

    if values["cancel"]:
        st.session_state.show_form = False
        st.rerun()

    if values["submitted"]:
        missing = validate_ticket(ticket_type, values)

        if missing:
            st.error("Please fill in: " + ", ".join(missing))
            return

        new_id = save_ticket(ticket_type, values)

        st.session_state.view_ticket_id = new_id
        st.session_state.show_form = False

        clear_ai_fields()
        st.session_state.pop("create_subject", None)

        st.success(f"{ticket_type} #{new_id} created successfully.")
        st.switch_page("pages/View_Ticket.py")