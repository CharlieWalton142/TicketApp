import streamlit as st

# ---------- Basic user helpers ----------

def get_current_user():
    """Return the current user dict from session, or None."""
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return get_current_user() is not None


def get_role():
    u = get_current_user()
    if not u:
        return None
    return (u.get("role") or "").strip().lower()


def is_admin() -> bool:
    return get_role() == "admin"


# ---------- Access control guards ----------

def require_login():
    """
    Redirect to Login page if no user in session.
    Use this at the top of every page except Login.
    """
    if not is_logged_in():
        st.switch_page("pages/Login.py")


def require_admin():
    """
    Ensure there is a logged-in admin.
    If not logged in -> send to Login.
    If logged in but not admin -> show error and stop.
    """
    if not is_logged_in():
        st.switch_page("pages/Login.py")

    if not is_admin():
        st.error("You do not have permission to view this page.")
        st.page_link("Home.py", label="⬅ Back to Home")
        st.stop()


# ---------- Sidebar visibility helpers ----------

def hide_login_link_if_logged_in():
    """
    Once logged in, hide the Login page link from the sidebar.
    Call this on all *non-login* pages.
    """
    if not is_logged_in():
        return

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


def hide_other_pages_on_login():
    """
    On the Login page, hide all other pages from the sidebar
    so only 'Login' is visible before authentication.
    """
    st.markdown(
        """
        <style>
        /* Hide home, tickets, view ticket, admin while on login page */
        [data-testid="stSidebarNav"] li a[href*="Home"] { display: none !important; }
        [data-testid="stSidebarNav"] li a[href*="Tickets"] { display: none !important; }
        [data-testid="stSidebarNav"] li a[href*="View_Ticket"] { display: none !important; }
        [data-testid="stSidebarNav"] li a[href*="Admin"] { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hide_admin_page_for_non_admin():
    """
    On general pages, hide the Admin page link in the sidebar for non-admin users.
    Call this after login on normal pages (Home, Tickets, View_Ticket).
    """
    if not is_logged_in():
        return

    if is_admin():
        # Admins SHOULD see the Admin page link
        return

    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] li a[href*="Admin"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )