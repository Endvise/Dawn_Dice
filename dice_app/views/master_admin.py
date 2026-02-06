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

    if not user:
        st.error("User information not found. Please log in again.")
        return

    st.title("Admin Account Management")
    st.markdown("---")

    admins = db.list_admins(role="admin")

    total_admins = len(admins)
    active_admins = len([a for a in admins if a.get("is_active")])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Admins", f"{total_admins}")

    with col2:
        st.metric("Active Admins", f"{active_admins}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Admin List", "Add Admin", "Promote/Demote Users"])

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

    with tab3:
        st.markdown("### Promote/Demote Users")
        st.info(
            "Only Master accounts can promote users to Admin or demote Admins to users."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Promote User to Admin")

            users = db.list_users()
            admins = db.list_admins()
            admin_ids = [a.get("id") for a in admins]

            regular_users = [u for u in users if u.get("id") not in admin_ids]

            if regular_users:
                st.markdown(f"**Regular Users ({len(regular_users)})**")

                for user_item in regular_users:
                    with st.expander(
                        f"👤 {user_item.get('nickname', 'Unknown')} - {user_item.get('commander_number', 'N/A')}"
                    ):
                        st.markdown(f"""
                        - **Nickname**: {user_item.get("nickname", "Unknown")}
                        - **Commander ID**: {user_item.get("commander_number", "N/A")}
                        - **Server**: {user_item.get("server", "N/A")}
                        - **Alliance**: {user_item.get("alliance", "None") if user_item.get("alliance") else "None"}
                        """)

                        if st.button(
                            "Promote to Admin",
                            key=f"promote_{user_item['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"Promote {user_item.get('nickname', 'Unknown')} to Admin?"
                            ):
                                try:
                                    admin_data = {
                                        "username": user_item.get(
                                            "commander_number", ""
                                        ),
                                        "password_hash": user_item.get(
                                            "password_hash", ""
                                        ),
                                        "full_name": user_item.get("nickname", ""),
                                        "role": "admin",
                                        "server": user_item.get("server", ""),
                                        "alliance": user_item.get("alliance", ""),
                                    }
                                    result = db.insert("admins", admin_data)
                                    if result:
                                        st.success(
                                            f"Promoted {user_item.get('nickname', 'Unknown')} to Admin!"
                                        )
                                        st.rerun()
                                    else:
                                        st.error("Failed to promote user.")
                                except Exception as e:
                                    st.error(f"Error promoting: {e}")
            else:
                st.info("No regular users found.")

        with col2:
            st.markdown("#### Demote Admin to User")

            if admins:
                st.markdown(f"**Admins ({len(admins)})**")

                for admin in admins:
                    is_current_user = user.get("id") == admin.get("id")

                    with st.expander(
                        f"👑 {admin.get('nickname', 'Unknown')} - {admin.get('username', 'Unknown')}"
                    ):
                        st.markdown(f"""
                        - **Username**: {admin.get("username", "Unknown")}
                        - **Nickname**: {admin.get("nickname", "Unknown")}
                        - **Role**: {admin.get("role", "Unknown")}
                        - **Status**: {"Active" if admin.get("is_active") else "Inactive"}
                        """)

                        if is_current_user:
                            st.warning("You cannot demote yourself.")
                        elif st.button(
                            "Demote to User",
                            key=f"demote_{admin['id']}",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"Demote {admin.get('nickname', 'Unknown')} to regular user?"
                            ):
                                try:
                                    success = db.delete("admins", {"id": admin["id"]})
                                    if success:
                                        st.success(
                                            f"Demoted {admin.get('nickname', 'Unknown')} to User!"
                                        )
                                        st.rerun()
                                    else:
                                        st.error("Failed to demote admin.")
                                except Exception as e:
                                    st.error(f"Error demoting: {e}")
            else:
                st.info("No admins found.")

        st.markdown("---")
        st.markdown("""
        **Important Notes:**

        - **Promote**: User can log in with existing credentials (commander_number + password)
        - **Demote**: Admin is removed from admins table, loses all admin permissions
        - **Self-protection**: You cannot demote yourself
        """)

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

    st.markdown("---")
    st.markdown("### Change My Password")

    with st.form("admin_change_password_form"):
        old_password = st.text_input(
            "Current Password", type="password", key="admin_old_password"
        )
        new_password = st.text_input(
            "New Password",
            type="password",
            help="Minimum 8 characters",
            key="admin_new_password",
        )
        confirm_password = st.text_input(
            "Confirm New Password", type="password", key="admin_confirm_password"
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
                success, message = auth.change_admin_password(
                    user["id"], old_password, new_password
                )

                if success:
                    st.success(f"✅ {message}")
                    st.info("Please log in again with your new password.")
                    if st.button("Logout"):
                        auth.logout()
                else:
                    st.error(f"❌ {message}")
