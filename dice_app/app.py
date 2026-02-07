#!/usr/bin/env python3
"""
DaWn Dice Party - Main Application
"""

import streamlit as st
import auth
import database as db
import security_utils
import utils


def main():
    """Main application"""
    # Page settings
    st.set_page_config(
        page_title="DaWn Dice Party",
        page_icon="🎲",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Session initialization
    auth.init_session_state()

    # Developer tools block (except admin)
    security_utils.inject_devtools_block()

    # Sidebar
    with st.sidebar:
        st.title("🎲 DaWn Dice Party")
        st.markdown("by Entity")
        st.markdown("---")

        # Page selection (based on login status)
        if auth.is_authenticated():
            st.markdown("### 📋 Menu")

            # General user/admin/master common menu
            if auth.is_admin():
                # Admin page selection
                page = st.radio(
                    "Select Admin Page",
                    [
                        "01. 🏠 Home",
                        "02. 📝 Make Reservation",
                        "03. 📊 My Reservations",
                        "04. 📊 Dashboard",
                        "05. 🎲 Session Management",
                        "06. 🎯 Session Check-in",
                        "07. 🤖 Session Manager AI",
                        "08. 📋 Reservation Management",
                        "09. 👥 Participant Management",
                        "10. 🚫 Blacklist Management",
                        "11. 📢 Announcement Management",
                        "12. 📖 사용 가이드",
                        "13. 🔐 Change Password",
                    ],
                )
            else:
                # General user menu (English)
                page = st.radio(
                    "Select Page",
                    [
                        "01. 🏠 Home",
                        "02. 📝 Make Reservation",
                        "03. 📊 My Reservations",
                        "04. 📖 이용 방법",
                        "05. 📖 How to Use",
                        "06. 🔐 Change Password",
                    ],
                )

            # Admin page variable (compatibility)
            admin_page = None
            if auth.is_admin() and page in [
                "04. 📊 Dashboard",
                "05. 🎲 Session Management",
                "06. 🎯 Session Check-in",
                "07. 🤖 Session Manager AI",
                "08. 📋 Reservation Management",
                "09. 👥 Participant Management",
                "10. 🚫 Blacklist Management",
                "11. 📢 Announcement Management",
            ]:
                admin_page = page

            # Master-only menu
            if auth.is_master():
                st.markdown("---")
                st.markdown("### 👑 Master Menu")

                if st.button("👤 Admin Account Management"):
                    st.session_state["page"] = "admin_management"
                    st.rerun()

            # User info
            auth.show_user_info()

            # Timezone selector
            st.markdown("---")
            utils.show_timezone_selector()
        else:
            st.markdown("### 📋 Menu")
            page = "Login"

    # Main content area
    if auth.is_authenticated():
        # Check if user must change password - redirect to change password page
        user_id = st.session_state.get(auth.SESSION_KEYS.get("user_id"))
        if user_id:
            role = auth.get_current_role()
            if role == "user":
                user = db.get_user_by_id(str(user_id))
                if user and user.get("must_change_password"):
                    page = "🔐 Change Password"
                    st.warning(
                        "⚠️ Your password has been reset. Please change your password."
                    )

        # Page routing
        if page == "01. 🏠 Home":
            import views.home

            views.home.show()
        elif page == "02. 📝 Make Reservation":
            import views.reservation

            views.reservation.show()
        elif page == "03. 📊 My Reservations":
            import views.my_reservations

            views.my_reservations.show()
        elif page == "04. 📊 Dashboard":
            import views.admin_dashboard

            views.admin_dashboard.show()
        elif page == "05. 🎲 Session Management":
            import views.event_sessions

            views.event_sessions.show()
        elif page == "06. 🎯 Session Check-in":
            import views.session_checkin

            views.session_checkin.show()
        elif page == "07. 🤖 Session Manager AI":
            import views.session_manager

            views.session_manager.show()
        elif page == "08. 📋 Reservation Management":
            import views.admin_reservations

            views.admin_reservations.show()
        elif page == "09. 👥 Participant Management":
            import views.admin_participants

            views.admin_participants.show()
        elif page == "10. 🚫 Blacklist Management":
            import views.admin_blacklist

            views.admin_blacklist.show()
        elif page == "11. 📢 Announcement Management":
            import views.admin_announcements

            views.admin_announcements.show()
        elif page == "12. 📖 사용 가이드":
            import views.admin_user_guide

            views.admin_user_guide.show()
        elif page == "04. 📖 이용 방법":
            import views.user_guide_ko

            views.user_guide_ko.show()
        elif page == "05. 📖 How to Use":
            import views.user_guide_en

            views.user_guide_en.show()
        elif page in ("06. 🔐 Change Password", "13. 🔐 Change Password"):
            import views.change_password

            views.change_password.show()

        # Master-only page
        if auth.is_master():
            if st.session_state.get("page") == "admin_management":
                import views.master_admin

                views.master_admin.show()

    else:
        # Pre-login handling
        if st.session_state.get("show_register"):
            import views.register

            views.register.show()
        else:
            # Homepage
            import views.home

            views.home.show()


if __name__ == "__main__":
    main()
