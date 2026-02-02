#!/usr/bin/env python3
"""
Registration page
"""

import streamlit as st
import re
import database as db
import auth


# Commander ID validation
def validate_commander_id(commander_id: str) -> tuple[bool, str]:
    """
    Validate commander ID.

    Returns: (is_valid, error_message)
    """
    # Remove whitespace
    commander_id = commander_id.strip()

    # Check empty
    if not commander_id:
        return False, "Please enter your Commander ID."

    # Only digits allowed
    if not commander_id.isdigit():
        return False, "Commander ID must consist of numbers only."

    # Length check (10 digits)
    if len(commander_id) != 10:
        return False, "Commander ID must be 10 digits."

    # Duplicate check
    existing = db.get_user_by_commander_id(commander_id)
    if existing:
        return False, "This Commander ID is already registered."

    # Blacklist check
    blacklisted = db.check_blacklist(commander_id)
    if blacklisted:
        return (
            False,
            f"This Commander ID is on the blacklist. (Reason: {blacklisted.get('reason', 'N/A')})",
        )

    return True, ""


# Password validation
def validate_password(password: str, confirm_password: str) -> tuple[bool, str]:
    """
    Validate password.

    Returns: (is_valid, error_message)
    """
    # Length check
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    # Match check
    if password != confirm_password:
        return False, "Passwords do not match."

    return True, ""


def show():
    """Show registration page"""
    st.title("Sign Up")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### User Registration")
        st.info("Register using your Commander ID.")

        # Nickname
        nickname = st.text_input(
            "Nickname", key="reg_nickname", placeholder="Enter your nickname"
        )

        # Commander ID
        commander_id = st.text_input(
            "Commander ID", key="reg_commander_id", placeholder="10-digit number"
        )

        # Commander ID validation display
        if commander_id:
            is_valid, error_msg = validate_commander_id(commander_id)

            if is_valid:
                st.success("Valid Commander ID.")
            else:
                st.error(f"Invalid: {error_msg}")

        # Server
        server = st.text_input(
            "Server", key="reg_server", placeholder="Enter server name"
        )

        # Alliance (optional)
        alliance = st.text_input(
            "Alliance", key="reg_alliance", placeholder="Enter your alliance if any"
        )

        # Password
        password = st.text_input(
            "Password",
            type="password",
            key="reg_password",
            placeholder="Min 8 characters",
        )
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="reg_confirm_password"
        )

        # Password validation display
        if password and confirm_password:
            is_valid, error_msg = validate_password(password, confirm_password)

            if is_valid:
                st.success("Password is valid.")
            else:
                st.error(f"Invalid: {error_msg}")

        st.markdown("---")

        # Button area
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

        with col_btn2:
            # Sign up button
            if st.button("Sign Up", use_container_width=True, type="primary"):
                # Required fields check
                if not all(
                    [nickname, commander_id, server, password, confirm_password]
                ):
                    st.error("Please fill in all required fields.")
                    return

                # Commander ID validation
                is_valid_id, error_id = validate_commander_id(commander_id)
                if not is_valid_id:
                    st.error(error_id)
                    return

                # Password validation
                is_valid_pwd, error_pwd = validate_password(password, confirm_password)
                if not is_valid_pwd:
                    st.error(error_pwd)
                    return

                # Create user
                try:
                    user_id = db.create_user(
                        username=None,
                        commander_id=commander_id,
                        password=password,
                        role="user",
                        nickname=nickname,
                        server=server,
                        alliance=alliance if alliance else None,
                    )

                    st.success(f"Registration complete! (ID: {user_id})")
                    st.info("Please log in from the login page.")

                    # Go to login page
                    if st.button("Go to Login", use_container_width=True):
                        st.session_state["show_register"] = False
                        st.session_state["page"] = "home"
                        st.rerun()

                except Exception as e:
                    st.error(f"Error during registration: {e}")

            # Cancel button
            if st.button("Cancel", use_container_width=True):
                st.session_state["show_register"] = False
                st.session_state["page"] = "home"
                st.rerun()

        # Guide message
        st.markdown("---")
        st.markdown("""
        ### Registration Guide

        - **Commander ID**: Must be 10 digits
        - **Password**: Minimum 8 characters
        - **Alliance**: Optional
        - Commander IDs on the blacklist cannot register.
        """)
