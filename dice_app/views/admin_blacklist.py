#!/usr/bin/env python3
"""
Admin Blacklist Management Page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show blacklist management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Blacklist Management")
    st.markdown("---")

    # Statistics
    local_blacklist = db.list_blacklist(is_active=True)
    total_blacklisted = len(local_blacklist)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Local Blacklist", f"{total_blacklisted}")

    with col2:
        st.info("Google Sheets blacklist is also checked automatically.")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Blacklist List", "Add to Blacklist", "Inactive List"])

    # Tab 1: Blacklist list
    with tab1:
        st.markdown("### Active Blacklist")

        if local_blacklist:
            for bl in local_blacklist:
                with st.expander(
                    f"🚫 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **Commander ID**: {bl["commander_id"]}
                        **Nickname**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                        **Reason**: {bl["reason"] if bl["reason"] else "N/A"}
                        **Added At**: {bl["added_at"]}
                        """)

                        if bl.get("added_by"):
                            if bl.get("added_by"):
                                adder = db.get_user_by_id(bl["added_by"])
                                if adder:
                                    st.info(
                                        f"Added by: {adder.get('nickname', adder.get('username', 'Unknown'))}"
                                    )

                    with col2:
                        st.markdown("### Actions")

                        if st.button(
                            "Deactivate",
                            key=f"deactivate_{bl['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.remove_from_blacklist(bl["commander_id"])
                                st.success("Removed from blacklist.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error removing: {e}")
        else:
            st.info("No active blacklist entries.")

    # Tab 2: Add to blacklist
    with tab2:
        st.markdown("### Add to Blacklist")

        col1, col2 = st.columns([1, 2])

        with col1:
            commander_id = st.text_input("Commander ID", placeholder="10-digit number")

            if commander_id:
                existing = db.check_blacklist(commander_id)
                if existing:
                    st.error(
                        f"Already on blacklist. (Reason: {existing.get('reason', 'N/A')})"
                    )
                else:
                    st.success("New Commander ID.")

            nickname = st.text_input("Nickname", placeholder="Optional")
            reason = st.text_area(
                "Blacklist Reason", placeholder="Required", height=100
            )

        with col2:
            st.markdown("### Guide")

            st.markdown("""
            - **Commander ID**: 10-digit number (required)
            - **Nickname**: Optional
            - **Reason**: Reason for blacklist (required)

            Users on blacklist:
            - Cannot make reservations
            - Cannot register
            - Existing reservations cancelled automatically
            """)

        st.markdown("---")
        if st.button("Add to Blacklist", type="primary", use_container_width=True):
            if not commander_id:
                st.error("Enter Commander ID.")
                return

            if not reason:
                st.error("Enter blacklist reason.")
                return

            try:
                db.add_to_blacklist(
                    commander_id=commander_id,
                    nickname=nickname if nickname else None,
                    reason=reason,
                    added_by=user["id"],
                )

                st.success(f"{commander_id} added to blacklist.")

                affected_reservations = db.list_reservations()
                affected_count = len(
                    [
                        r
                        for r in affected_reservations
                        if r["commander_id"] == commander_id
                    ]
                )

                if affected_count > 0:
                    st.warning(f"{affected_count} reservations affected.")

                st.rerun()

            except Exception as e:
                st.error(f"Error adding: {e}")

    # Tab 3: Inactive list
    with tab3:
        st.markdown("### Inactive Blacklist")

        inactive_blacklist = db.list_blacklist(is_active=False)

        if inactive_blacklist:
            st.info(f"{len(inactive_blacklist)} inactive blacklist entries.")

            for bl in inactive_blacklist:
                with st.expander(
                    f"🔓 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **Commander ID**: {bl["commander_id"]}
                    **Nickname**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                    **Reason**: {bl["reason"] if bl["reason"] else "N/A"}
                    **Added At**: {bl["added_at"]}
                    """)

                    if st.button(
                        "Restore", key=f"restore_{bl['id']}", use_container_width=True
                    ):
                        try:
                            from database import execute_query

                            execute_query(
                                """
                                UPDATE blacklist SET is_active = 1 WHERE id = ?
                            """,
                                (bl["id"],),
                            )

                            execute_query(
                                """
                                UPDATE reservations SET is_blacklisted = 0, blacklist_reason = NULL
                                WHERE commander_id = ?
                            """,
                                (bl["commander_id"],),
                            )

                            st.success("Blacklist restored.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error restoring: {e}")

                    if is_master:
                        if st.button(
                            "Delete Permanently",
                            key=f"permanent_delete_{bl['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            confirm_delete = st.checkbox(
                                "I understand this cannot be undone",
                                key=f"confirm_permanent_{bl['id']}",
                            )
                            if confirm_delete:
                                try:
                                    from database import execute_query

                                    execute_query(
                                        "DELETE FROM blacklist WHERE id = ?",
                                        (bl["id"],),
                                    )
                                    st.success("Permanently deleted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {e}")
        else:
            st.info("No inactive blacklist entries.")

    st.markdown("---")

    st.markdown("""
    ### Admin Guide

    - **Active**: Commander ID cannot reserve/register
    - **Deactivate**: Temporarily unblock (can be restored)
    - **Delete Permanently**: Complete removal (cannot restore)
    - **Google Sheets**: External blacklist is also checked automatically

    Only master accounts can permanently delete.
    """)
