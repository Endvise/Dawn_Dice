#!/usr/bin/env python3
"""
Authentication Management Module
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import database as db
import config


# Session state keys
SESSION_KEYS = {
    "authenticated": "dice_authenticated",
    "user_id": "dice_user_id",
    "username": "dice_username",
    "role": "dice_role",
    "nickname": "dice_nickname",
    "login_time": "dice_login_time",
    "access_token": "dice_access_token",  # Supabase access token
}


def init_session_state():
    """Initialize session state."""
    for key, session_key in SESSION_KEYS.items():
        if session_key not in st.session_state:
            st.session_state[session_key] = None


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login - authenticates against Supabase admins/users tables.
    Returns: (success, message)
    """
    # Get auth config
    auth_config = config.get_config()["auth"]
    supabase_config = config.get_config()["supabase"]

    # Check if Supabase Auth is enabled (recommended disabled for now)
    use_supabase_auth = supabase_config["use_auth"]

    if use_supabase_auth:
        # Supabase Auth 시도
        success, message, access_token = db.supabase_sign_in(username, password)

        if success and access_token:
            user_data_success, user_data = db.supabase_get_user(access_token)

            if user_data_success and user_data:
                st.session_state[SESSION_KEYS["authenticated"]] = True
                st.session_state[SESSION_KEYS["user_id"]] = user_data.get("id")
                st.session_state[SESSION_KEYS["username"]] = username
                st.session_state[SESSION_KEYS["role"]] = "user"
                st.session_state[SESSION_KEYS["nickname"]] = ""
                st.session_state[SESSION_KEYS["login_time"]] = datetime.now()
                st.session_state[SESSION_KEYS["access_token"]] = access_token
                return True, "Login successful!"

        st.warning("Supabase Auth failed, using local auth...")

    # Local auth (bcrypt) - based on admins/users tables
    # Check admins table first (master/admin)
    admin = db.get_admin_by_username(username)

    # If no admin account, try users table
    if not admin:
        # Check users table (regular users)
        user = db.get_user_by_commander_number(username)

        if not user:
            return False, "User not found."

        if not user.get("is_active"):
            return False, "Account is disabled."

        if not db.verify_password(password, user["password_hash"]):
            return False, "Invalid password."

        st.session_state[SESSION_KEYS["authenticated"]] = True
        st.session_state[SESSION_KEYS["user_id"]] = user["id"]
        st.session_state[SESSION_KEYS["username"]] = user.get("commander_number")
        st.session_state[SESSION_KEYS["role"]] = "user"
        st.session_state[SESSION_KEYS["nickname"]] = user.get("nickname", "")
        st.session_state[SESSION_KEYS["login_time"]] = datetime.now()
        st.session_state[SESSION_KEYS["access_token"]] = None

        return True, "Login successful!"

    # Admin account login
    if admin:
        if not db.verify_password(password, admin["password_hash"]):
            return False, "Invalid password."

        db.update_admin_last_login(admin["id"])

        st.session_state[SESSION_KEYS["authenticated"]] = True
        st.session_state[SESSION_KEYS["user_id"]] = admin["id"]
        st.session_state[SESSION_KEYS["username"]] = admin.get("username")
        st.session_state[SESSION_KEYS["role"]] = admin.get("role", "admin")
        st.session_state[SESSION_KEYS["nickname"]] = admin.get("full_name", "")
        st.session_state[SESSION_KEYS["login_time"]] = datetime.now()
        st.session_state[SESSION_KEYS["access_token"]] = None

        return True, "Login successful!"

    # Should not reach here, but return False as fallback
    return False, "Authentication failed."


def logout():
    """Logout."""
    for key, session_key in SESSION_KEYS.items():
        st.session_state[session_key] = None
    st.rerun()


def change_user_password(
    user_id: str, old_password: str, new_password: str
) -> tuple[bool, str]:
    """
    Change user password.
    Returns: (success, message)
    """
    user = db.get_user_by_id(user_id)

    if not user:
        return False, "User not found."

    # Verify old password
    if not db.verify_password(old_password, user["password_hash"]):
        return False, "Current password is incorrect."

    # Hash new password and update
    new_hash = db.hash_password(new_password)
    success = db.update_user_password(user_id, new_hash)

    if success:
        return True, "Password changed successfully!"
    else:
        return False, "Failed to update password."


def change_admin_password(
    admin_id: str, old_password: str, new_password: str
) -> tuple[bool, str]:
    """
    Change admin password.
    Returns: (success, message)
    """
    admin = db.get_admin_by_id(admin_id)

    if not admin:
        return False, "Admin account not found."

    # Verify old password
    if not db.verify_password(old_password, admin["password_hash"]):
        return False, "Current password is incorrect."

    # Hash new password and update
    new_hash = db.hash_password(new_password)
    success = db.update_admin_password(admin_id, new_hash)

    if success:
        return True, "Password changed successfully!"
    else:
        return False, "Failed to update password."


def is_authenticated() -> bool:
    """Check authentication."""
    authenticated = st.session_state.get(SESSION_KEYS["authenticated"])
    if not authenticated:
        return False

    # Check session timeout
    login_time = st.session_state.get(SESSION_KEYS["login_time"])
    if login_time:
        session_config = config.get_config()["session"]
        timeout_minutes = session_config["timeout_minutes"]
        if (datetime.now() - login_time) > timedelta(minutes=timeout_minutes):
            logout()
            return False

    return True


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return current user info."""
    if not is_authenticated():
        return None

    user_id = st.session_state.get(SESSION_KEYS["user_id"])
    role = st.session_state.get(SESSION_KEYS["role"])

    if user_id:
        # admin/master are queried from admins table
        if role in ["master", "admin"]:
            return db.get_admin_by_id(user_id)
        # Regular users are queried from users table
        else:
            return db.get_user_by_id(user_id)
    return None


def get_current_user_id() -> Optional[int]:
    """Return current user ID."""
    return st.session_state.get(SESSION_KEYS["user_id"])


def get_current_role() -> Optional[str]:
    """Return current user role."""
    return st.session_state.get(SESSION_KEYS["role"])


def is_master() -> bool:
    """Check master permissions."""
    return get_current_role() == "master"


def is_admin() -> bool:
    """Check admin permissions."""
    role = get_current_role()
    return role in ["master", "admin"]


def is_user() -> bool:
    """Check if regular user."""
    return get_current_role() == "user"


def require_auth(required_role: Optional[str] = None) -> bool:
    """
    Check authentication and permission.
    Returns: access permission
    """
    # Check authentication
    if not is_authenticated():
        return False

    # Check role
    if required_role:
        current_role = get_current_role()

        if required_role == "master":
            return is_master()
        elif required_role == "admin":
            return is_admin()
        elif required_role == "user":
            return True  # All authenticated users can access

    return True


def show_login_page():
    """Display login page."""
    st.title("🎲 DaWn Dice Party")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Login")

        login_method = st.radio(
            "Login Method",
            ["User ID / Commander ID", "Master Account"],
            horizontal=True,
        )

        username = st.text_input("ID or Commander ID", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            success, message = login(username, password)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.markdown("---")
        st.markdown("### Don't have an account?")

        if st.button("Register", use_container_width=True):
            st.session_state["show_register"] = True
            st.rerun()


def require_login(required_role: Optional[str] = None, redirect_to: str = "login"):
    """
    Decorator for pages requiring login.
    """
    if not is_authenticated():
        show_login_page()
        st.stop()

    if required_role:
        current_role = get_current_role()

        if required_role == "master" and not is_master():
            st.error("Master权限 required.")
            st.stop()
        elif required_role == "admin" and not is_admin():
            st.error("Admin权限 required.")
            st.stop()


def show_user_info():
    """Display user info."""
    user = get_current_user()

    if user:
        role = get_current_role() or ""
        role_labels = {"master": "👑 Master", "admin": "🛡️ Admin", "user": "👤 User"}
        role_label = role_labels.get(role, role)

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.text(
            f"Name: {user.get('nickname', user.get('commander_number', 'Unknown'))}"
        )
        st.sidebar.text(f"Role: {role_label}")

        if st.sidebar.button("Logout"):
            logout()


def get_user_statistics() -> Dict[str, Any]:
    """Return user statistics."""
    user_id = get_current_user_id()
    if is_user() and user_id:
        my_reservations = db.list_reservations(user_id=str(user_id))
        total_reservations = len(my_reservations)
    else:
        total_reservations = len(db.list_reservations())

    return {
        "total_reservations": total_reservations,
        "pending_reservations": 0,  # Status field removed
        "is_blacklisted": False,
    }
