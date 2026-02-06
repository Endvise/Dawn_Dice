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
                        "🏠 Home",
                        "📝 Make Reservation",
                        "📊 My Reservations",
                        "📊 Dashboard",
                        "🎲 Session Management",
                        "🎯 Session Check-in",
                        "🤖 Session Manager AI",
                        "📋 Reservation Management",
                        "👥 Participant Management",
                        "🚫 Blacklist Management",
                        "📢 Announcement Management",
                    ],
                )
            else:
                # General user menu (English)
                page = st.radio(
                    "Select Page",
                    [
                        "🏠 Home",
                        "📝 Make Reservation",
                        "📊 My Reservations",
                    ],
                )

            # Admin page variable (compatibility)
            admin_page = None
            if auth.is_admin() and page in [
                "📊 Dashboard",
                "🎲 Session Management",
                "🎯 Session Check-in",
                "🤖 Session Manager AI",
                "📋 Reservation Management",
                "👥 Participant Management",
                "🚫 Blacklist Management",
                "📢 Announcement Management",
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

        # Change Password button (at bottom)
        st.markdown("---")
        if st.button("🔐 Change Password", use_container_width=True):
            st.session_state["show_change_password"] = True
            st.rerun()
        else:
            st.markdown("### 📋 Menu")
            page = "Login"

    # Main content area
    if auth.is_authenticated():
        # Check if change password page is active (full-page mode)
        if st.session_state.get("show_change_password"):
            import views.change_password

            views.change_password.show()
        else:
            # Page routing
            if page == "🏠 Home":
                import views.home

                views.home.show()
            elif page == "📝 Make Reservation":
                import views.reservation

                views.reservation.show()
            elif page == "📊 My Reservations":
                import views.my_reservations

                views.my_reservations.show()
            elif page == "📊 Dashboard":
                import views.admin_dashboard

                views.admin_dashboard.show()
            elif page == "🎲 Session Management":
                import views.event_sessions

                views.event_sessions.show()
            elif page == "🎯 Session Check-in":
                import views.session_checkin

                views.session_checkin.show()
            elif page == "🤖 Session Manager AI":
                import views.session_manager

                views.session_manager.show()
            elif page == "📋 Reservation Management":
                import views.admin_reservations

                views.admin_reservations.show()
            elif page == "👥 Participant Management":
                import views.admin_participants

                views.admin_participants.show()
            elif page == "🚫 Blacklist Management":
                import views.admin_blacklist

                views.admin_blacklist.show()
            elif page == "📢 Announcement Management":
                import views.admin_announcements

                views.admin_announcements.show()

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
