#!/usr/bin/env python3
"""
Master Admin Account Management Page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show master admin account management page"""
    auth.require_login(required_role="master")

    user = auth.get_current_user()

    # user가 None인 경우 처리
    if not user:
        st.error("User information not found. Please log in again.")
        return

    st.title("Admin Account Management")
    st.markdown("---")

    # admins 테이블에서 관리자 목록 조회
    admins = db.list_admins(role="admin")

    total_admins = len(admins)
    active_admins = len([a for a in admins if a.get("is_active")])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Admins", f"{total_admins}")

    with col2:
        st.metric("Active Admins", f"{active_admins}")

    st.markdown("---")

    tab1, tab2 = st.tabs(["Admin List", "Add Admin"])

    with tab1:
        st.markdown("### Admin List")

        if admins:
            for admin in admins:
                status_badge = "✅" if admin.get("is_active") else "⏳"

                with st.expander(
                    f"{status_badge} {admin.get('username', 'Unknown')} - {admin.get('nickname', 'Unknown')}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **Username**: {admin.get("username", "Unknown")}
                        **Nickname**: {admin.get("nickname", "Unknown")}
                        **Server**: {admin.get("server", "N/A")}
                        **Alliance**: {admin.get("alliance", "N/A") if admin.get("alliance") else "None"}
                        **Role**: {admin.get("role", "Unknown")}
                        **Status**: {"Active" if admin.get("is_active") else "Inactive"}
                        **Created At**: {admin.get("created_at", "N/A")}
                        **Last Login**: {admin.get("last_login", "N/A") if admin.get("last_login") else "None"}
                        """)

                        if admin.get("failed_attempts", 0) > 0:
                            st.warning(f"Login failures: {admin['failed_attempts']}")

                    with col2:
                        st.markdown("### Actions")

                        if st.button(
                            "Reset Password",
                            key=f"reset_pwd_{admin['id']}",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"Reset password for {admin.get('username', 'Unknown')}?"
                            ):
                                try:
                                    import secrets

                                    new_password = secrets.token_urlsafe(12)

                                    db.update_user(admin["id"], password=new_password)

                                    st.success("Password reset.")
                                    st.code(
                                        f"New password: {new_password}", language=None
                                    )
                                except Exception as e:
                                    st.error(f"Error resetting: {e}")

                        if admin.get("is_active"):
                            if st.button(
                                "Deactivate",
                                key=f"deactivate_{admin['id']}",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    f"Deactivate {admin.get('username', 'Unknown')}?"
                                ):
                                    try:
                                        db.update_user(admin["id"], is_active=0)
                                        st.success("Deactivated.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deactivating: {e}")
                        else:
                            if st.button(
                                "Activate",
                                key=f"activate_{admin['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    db.update_user(admin["id"], is_active=1)
                                    st.success("Activated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error activating: {e}")

                        if st.button(
                            "Edit", key=f"edit_{admin['id']}", use_container_width=True
                        ):
                            st.session_state["edit_admin_id"] = admin["id"]
                            st.rerun()

                        if st.button(
                            "Delete",
                            key=f"delete_{admin['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"Delete {admin.get('username', 'Unknown')}?"
                            ):
                                try:
                                    db.delete_user(admin["id"])
                                    st.success("Deleted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {e}")
        else:
            st.info("No registered admins.")

    with tab2:
        st.markdown("### Add Admin")

        col1, col2 = st.columns([1, 2])

        with col1:
            username = st.text_input(
                "Username", placeholder="English/numbers", key="new_admin_username"
            )

            if username:
                existing = db.get_user_by_username(username)
                if existing:
                    st.error(f"Username already exists: {username}")
                else:
                    st.success("Username available.")

            nickname = st.text_input(
                "Nickname", placeholder="Required", key="new_admin_nickname"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Min 8 characters",
                key="new_admin_password",
            )
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="new_admin_confirm_password"
            )

            if password and confirm_password:
                if password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    st.success("Password valid.")

            server = st.text_input(
                "Server", placeholder="#095 woLF", key="new_admin_server"
            )
            alliance = st.text_input(
                "Alliance", placeholder="Optional", key="new_admin_alliance"
            )

        with col2:
            st.markdown("### Guide")

            st.markdown("""
            - **Username**: Admin login ID
            - **Nickname**: Display name (required)
            - **Password**: Min 8 characters
            - **Server**: Affiliated server (optional)
            - **Alliance**: Affiliated alliance (optional)

            **Permissions:**
            - Approve/reject reservations
            - Manage participants
            - Manage blacklist
            - Create announcements

            Only master accounts can create/delete admins.
            """)

        st.markdown("---")
        if st.button("Add Admin", type="primary", use_container_width=True):
            if not username:
                st.error("Enter username.")
                return

            if not nickname:
                st.error("Enter nickname.")
                return

            if not password or not confirm_password:
                st.error("Enter password.")
                return

            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            if len(password) < 8:
                st.error("Password must be at least 8 characters.")
                return

            try:
                admin_id = db.create_admin(
                    username=username,
                    password=password,
                    full_name=nickname,
                    role="admin",
                )

                st.success(f"Admin created! (ID: {admin_id})")
                st.info("New admin can log in immediately.")
                st.rerun()

            except Exception as e:
                st.error(f"Error creating: {e}")

    st.markdown("---")

    st.markdown("""
    ### Master Guide

    - **Admin Permissions**: Manage reservations/participants/blacklist/announcements
    - **Master Permissions**: All admin permissions + manage admin accounts
    - **Password**: Min 8 characters, master can reset

    **Security Tips:**
    - Change admin passwords regularly
    - Investigate suspicious activity immediately
    - Delete unnecessary admins
    """)

    st.markdown("---")
    st.markdown("### Current Master Account")

    st.info(f"""
    **Username**: {user.get("username", "Unknown")}
    **Nickname**: {user.get("nickname", "Unknown")}
    **Login Time**: {st.session_state.get("dice_login_time", "Unknown")}
    """)
