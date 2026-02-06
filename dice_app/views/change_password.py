#!/usr/bin/env python3
"""
Change Password page - Users can change their password
"""

import streamlit as st
import auth


def show():
    """Show change password page for users"""
    auth.require_login()

    user = auth.get_current_user()

    if not user:
        st.error("User information not found. Please log in again.")
        return

    # Only regular users can use this page
    if auth.is_admin():
        st.warning("Administrators should use the admin password change page.")
        st.info("Go to Admin Dashboard → Settings → Change Password")
        if st.button("Go to Admin Dashboard"):
            st.session_state["page"] = "Admin Dashboard"
            st.rerun()
        return

    st.title("🔐 Change Password")
    st.markdown("---")

    st.markdown(f"**Account:** {user.get('commander_number', 'Unknown')}")

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
            # Validation
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
                # Attempt to change password
                success, message = auth.change_user_password(
                    user["id"], old_password, new_password
                )

                if success:
                    st.success(f"✅ {message}")
                    st.info("Please log in again with your new password.")
                    if st.button("Logout"):
                        auth.logout()
                else:
                    st.error(f"❌ {message}")

    st.markdown("---")

    # Password requirements
    st.markdown("""
    **Password Requirements:**
    - Minimum 8 characters
    - Different from current password
    """)

    # Back button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state["page"] = "My Reservations"
            st.rerun()
