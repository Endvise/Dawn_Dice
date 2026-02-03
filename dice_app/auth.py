#!/usr/bin/env python3
"""
Authentication Management Module
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import database as db


# Session state keys
SESSION_KEYS = {
    "authenticated": "dice_authenticated",
    "user_id": "dice_user_id",
    "username": "dice_username",
    "role": "dice_role",
    "nickname": "dice_nickname",
    "login_time": "dice_login_time",
}


def init_session_state():
    """Initialize session state."""
    for key, session_key in SESSION_KEYS.items():
        if session_key not in st.session_state:
            st.session_state[session_key] = None


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login.
    Returns: (success, message)
    """
    # Find user
    user = db.get_user_by_username(username)

    if not user:
        # Also try commander ID
        user = db.get_user_by_commander_id(username)

    if not user:
        return False, "User not found."

    # Check if account is disabled
    if not user.get("is_active"):
        return False, "Account is disabled."

    # Check login attempts
    max_attempts = st.secrets.get("MAX_LOGIN_ATTEMPTS", 5)
    if user.get("failed_attempts", 0) >= max_attempts:
        return False, "Too many failed login attempts. Contact admin."

    # Verify password
    if not db.verify_password(password, user["password_hash"]):
        # Increase failed attempts
        db.update_user(user["id"], failed_attempts=user.get("failed_attempts", 0) + 1)
        remaining = max_attempts - user.get("failed_attempts", 0) - 1
        return (
            False,
            f"Invalid password. ({remaining} attempts remaining)",
        )

    # Login successful
    db.update_user(user["id"], failed_attempts=0, last_login=datetime.now())

    # Set session state
    st.session_state[SESSION_KEYS["authenticated"]] = True
    st.session_state[SESSION_KEYS["user_id"]] = user["id"]
    st.session_state[SESSION_KEYS["username"]] = user.get("username") or user.get(
        "commander_id"
    )
    st.session_state[SESSION_KEYS["role"]] = user["role"]
    st.session_state[SESSION_KEYS["nickname"]] = user.get("nickname", "")
    st.session_state[SESSION_KEYS["login_time"]] = datetime.now()

    return True, "Login successful!"


def logout():
    """Logout."""
    for key, session_key in SESSION_KEYS.items():
        st.session_state[session_key] = None
    st.rerun()


def is_authenticated() -> bool:
    """Check authentication."""
    authenticated = st.session_state.get(SESSION_KEYS["authenticated"])
    if not authenticated:
        return False

    # Check session timeout
    login_time = st.session_state.get(SESSION_KEYS["login_time"])
    if login_time:
        timeout_minutes = st.secrets.get("SESSION_TIMEOUT_MINUTES", 60)
        if (datetime.now() - login_time) > timedelta(minutes=timeout_minutes):
            logout()
            return False

    return True


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return current user info."""
    if not is_authenticated():
        return None

    user_id = st.session_state.get(SESSION_KEYS["user_id"])
    if user_id:
        return db.get_user_by_id(user_id)
    return None


def get_current_user_id() -> Optional[int]:
    """Return current user ID."""
    return st.session_state.get(SESSION_KEYS["user_id"])


def get_current_role() -> Optional[str]:
    """Return current user role."""
    return st.session_state.get(SESSION_KEYS["role"])


def is_master() -> bool:
    """Check master权限."""
    return get_current_role() == "master"


def is_admin() -> bool:
    """Check admin权限."""
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
        role_labels = {"master": "👑 Master", "admin": "🛡️ Admin", "user": "👤 User"}

        role_label = role_labels.get(user["role"], user["role"])

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.text(
            f"Name: {user.get('nickname', user.get('username', 'Unknown'))}"
        )
        st.sidebar.text(f"Role: {role_label}")

        if st.sidebar.button("Logout"):
            logout()


def get_user_statistics() -> Dict[str, Any]:
    """Return user statistics."""
    # Reservation count
    if is_user():
        my_reservations = db.list_reservations(user_id=get_current_user_id())
        total_reservations = len(my_reservations)
        pending_reservations = len(
            [r for r in my_reservations if r["status"] == "pending"]
        )
    else:
        total_reservations = len(db.list_reservations())
        pending_reservations = len(db.list_reservations(status="pending"))

    return {
        "total_reservations": total_reservations,
        "pending_reservations": pending_reservations,
        "is_blacklisted": False,
    }
