#!/usr/bin/env python3
"""
Change Password page - All users can change their password
"""

import streamlit as st
import auth


def show():
    """Show change password page for all users"""
    auth.require_login()

    user = auth.get_current_user()

    if not user:
        st.error("User information not found. Please log in again.")
        return

    # Full-page mode - hide sidebar but show page navigation
    st.markdown(
        """
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Page navigation
    pages = [
        "🔐 Change Password",
        "🏠 Home",
        "📝 Make Reservation",
        "📊 My Reservations",
    ]

    # Add admin pages if user is admin
    if auth.is_admin():
        admin_pages = [
            "📊 Dashboard",
            "🎲 Session Management",
            "🎯 Session Check-in",
            "🤖 Session Manager AI",
            "📋 Reservation Management",
            "👥 Participant Management",
            "🚫 Blacklist Management",
            "📢 Announcement Management",
        ]
        pages.extend(admin_pages)

    # Page selector
    selected_page = st.selectbox("Go to Page", pages, index=0, key="page_selector")

    # Navigate to selected page
    if selected_page != "🔐 Change Password":
        st.session_state["show_change_password"] = False
        page_map = {
            "🏠 Home": "🏠 Home",
            "📝 Make Reservation": "📝 Make Reservation",
            "📊 My Reservations": "📊 My Reservations",
            "📊 Dashboard": "📊 Dashboard",
            "🎲 Session Management": "🎲 Session Management",
            "🎯 Session Check-in": "🎯 Session Check-in",
            "🤖 Session Manager AI": "🤖 Session Manager AI",
            "📋 Reservation Management": "📋 Reservation Management",
            "👥 Participant Management": "👥 Participant Management",
            "🚫 Blacklist Management": "🚫 Blacklist Management",
            "📢 Announcement Management": "📢 Announcement Management",
        }
        st.session_state["page"] = page_map.get(selected_page, "🏠 Home")
        st.rerun()
        return

    st.title("🔐 Change Password")
    st.markdown(f"**Account:** {user.get('commander_number', 'Unknown')}")
    st.markdown("---")

    # Password change form
    with st.form("change_password_form"):
        old_password = st.text_input(
            "Current Password", type="password", key="old_password"
        )
        new_password = st.text_input(
            "New Password",
            type="password",
            help="Minimum 8 characters",
            key="new_password",
        )
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="confirm_password"
        )

        submitted = st.form_submit_button(
            "Change Password", use_container_width=True, type="primary"
        )

        if submitted:
            if not old_password:
                st.error("Please enter your current password.")
            elif not new_password:
                st.error("Please enter a new password.")
            elif len(new_password) < 8:
                st.error("New password must be at least 8 characters.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            elif old_password == new_password:
                st.error("New password must be different from current password.")
            else:
                success, message = auth.change_user_password(
                    user["id"], old_password, new_password
                )

                if success:
                    st.success("Password changed successfully!")
                    st.info("Please log in again with your new password.")
                    if st.button("Logout"):
                        auth.logout()
                else:
                    st.error(f"Error: {message}")

    st.markdown("---")
    st.markdown("""
    **Password Requirements:**
    - Minimum 8 characters
    - Different from current password
    """)
