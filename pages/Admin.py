# pages/Admin.py
import streamlit as st
from db import (
    init_db,
    list_users_full,
    create_user,
    update_user_role,
    delete_user,
)
from sidebar import require_admin, hide_login_link_if_logged_in, get_current_user

st.set_page_config(page_title="User Administration", page_icon="🛠️", layout="wide")
init_db()

# -------------------------------------------------
# Auth & role check
# -------------------------------------------------
current_user = st.session_state.get("user")
if not current_user:
    st.switch_page("pages/Login.py")

require_admin()
hide_login_link_if_logged_in()

st.title("🛠️ User Administration")
st.caption(f"Signed in as {current_user['username']} (admin)")

st.divider()

# -------------------------------------------------
# Section 1: Create new user
# -------------------------------------------------
st.subheader("Create new user")

with st.form("create_user_form", clear_on_submit=True):
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    new_password2 = st.text_input("Confirm Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"])

    create_submitted = st.form_submit_button("➕ Create user", use_container_width=False)

if create_submitted:
    errors = []
    if not new_username.strip():
        errors.append("Username is required.")
    if len(new_password) < 8:
        errors.append("Password must be at least 8 characters.")
    if new_password != new_password2:
        errors.append("Passwords do not match.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        ok = create_user(new_username.strip(), new_password, new_role)
        if ok:
            st.success(f"User '{new_username}' created with role '{new_role}'.")
        else:
            st.error(f"Username '{new_username}' already exists.")

st.divider()

# -------------------------------------------------
# Section 2: Existing users
# -------------------------------------------------
st.subheader("Existing users")

users = list_users_full()
if not users:
    st.info("No users found.")
else:
    # Display users in a table-like layout with controls
    header_cols = st.columns([1, 3, 2, 3, 2, 2])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Username**")
    header_cols[2].markdown("**Role**")
    header_cols[3].markdown("**Created at**")
    header_cols[4].markdown("**Change role**")
    header_cols[5].markdown("**Delete**")

    st.write("---")

    for u in users:
        uid = u["id"]
        uname = u["username"]
        urole = u["role"]
        ucreated = u["created_at"]

        cols = st.columns([1, 3, 2, 3, 2, 2])
        cols[0].write(uid)
        cols[1].write(uname)
        cols[2].write(urole)
        cols[3].write(ucreated)

        # Change role selectbox + button
        with cols[4]:
            new_role_sel = st.selectbox(
                f"Role_{uid}",
                ["user", "admin"],
                index=["user", "admin"].index(urole),
                key=f"role_sel_{uid}",
            )
            if new_role_sel != urole:
                if st.button("Update", key=f"update_role_{uid}", use_container_width=True):
                    update_user_role(uid, new_role_sel)
                    st.success(f"Updated role for '{uname}' to '{new_role_sel}'.")
                    st.rerun()

        # Delete user (but not yourself)
        with cols[5]:
            if uid == current_user["id"]:
                st.caption("Cannot delete yourself")
            else:
                if st.button("Delete", key=f"del_user_{uid}", use_container_width=True):
                    st.session_state["confirm_delete_user"] = uid

    # Confirm delete modal-style block
    confirm_id = st.session_state.get("confirm_delete_user")
    if confirm_id:
        st.warning(f"Are you sure you want to delete user ID {confirm_id}? This cannot be undone.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, delete user"):
                delete_user(confirm_id)
                st.success(f"User {confirm_id} deleted.")
                st.session_state["confirm_delete_user"] = None
                st.rerun()
        with c2:
            if st.button("❌ Cancel"):
                st.session_state["confirm_delete_user"] = None
                st.rerun()