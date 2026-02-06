#!/usr/bin/env python3
"""
Admin Reservations Management Page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show admin reservations management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Reservation Management")
    st.markdown("---")

    # Statistics (simplified schema - no status field)
    all_reservations = db.list_reservations()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total", len(all_reservations))

    with col2:
        st.metric("Pending", 0)  # No status field

    with col3:
        st.metric("Approved", len(all_reservations))  # All reservations are approved

    with col4:
        st.metric("Rejected", 0)  # No status field

    with col5:
        st.metric("Blacklisted", 0)  # No is_blacklisted field

    st.markdown("---")

    # Filter
    st.markdown("### Filter")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["All", "Pending", "Approved", "Rejected", "Cancelled"],
            key="admin_status_filter",
        )

    with col2:
        blacklist_filter = st.selectbox(
            "Blacklist Filter",
            ["All", "Blacklisted", "Normal"],
            key="admin_blacklist_filter",
        )

    with col3:
        search_term = st.text_input("Search (Nickname/Commander ID)")

    st.markdown("---")

    # Reservation list
    filtered_reservations = []

    for res in all_reservations:
        # Status filter
        if status_filter != "All":
            status_map = {
                "Pending": "pending",
                "Approved": "approved",
                "Rejected": "rejected",
                "Cancelled": "cancelled",
            }

            if res["status"] != status_map[status_filter]:
                continue

        # Blacklist filter
        if blacklist_filter == "Blacklisted" and not res.get("is_blacklisted"):
            continue

        if blacklist_filter == "Normal" and res.get("is_blacklisted"):
            continue

        # Search filter
        if search_term:
            search_lower = search_term.lower()
            if search_lower not in res["nickname"].lower() and search_lower not in str(
                res["commander_id"]
            ):
                continue

        filtered_reservations.append(res)

    st.markdown(f"### Reservations ({len(filtered_reservations)})")

    if filtered_reservations:
        for res in filtered_reservations:
            # Status color
            status_color = {
                "pending": "🟡",
                "approved": "🟢",
                "rejected": "🔴",
                "cancelled": "⚪",
            }

            res_status = res.get("status") or "pending"
            status_label = status_color.get(res_status, "❓") + " " + res_status.upper()

            # Blacklist indicator
            blacklist_warning = " ⛔ Blacklisted" if res.get("is_blacklisted") else ""

            # Reservation card
            with st.expander(
                f"{status_label}{blacklist_warning} - {res['created_at'][:19]} (ID: {res['id']})"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Nickname**: {res.get("nickname", "Unknown")}
                    **Commander ID**: {res.get("commander_number", res.get("commander_id", "N/A"))}
                    **Server**: {res.get("server", "N/A")}
                    **Alliance**: {res.get("alliance", "None") or "None"}
                    **Applicant**: {res.get("user_nickname", res.get("user_role", "Unknown"))}
                    **Applied At**: {res.get("created_at", "N/A")}
                    **Status**: {res.get("status", "pending")}
                    """)

                    if res.get("approved_at"):
                        st.markdown(f"**Approved At**: {res['approved_at']}")

                    if res.get("notes"):
                        st.text(f"**Notes**: {res['notes']}")

                    if res.get("is_blacklisted"):
                        st.warning(
                            f"⛔ **Blacklist**: {res.get('blacklist_reason', 'N/A')}"
                        )

                with col2:
                    # Action buttons
                    st.markdown("### Actions")

                    if res.get("status") == "pending":
                        col_a1, col_a2 = st.columns(2)

                        with col_a1:
                            if st.button(
                                "Approve",
                                key=f"approve_{res['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    if user and user.get("id"):
                                        db.update_reservation_status(
                                            res["id"], "approved", user["id"]
                                        )
                                        st.success("Approved.")
                                        st.rerun()
                                    else:
                                        st.error("User session expired.")
                                except Exception as e:
                                    st.error(f"Error approving: {e}")

                        with col_a2:
                            if st.button(
                                "Reject",
                                key=f"reject_{res['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    db.update_reservation_status(
                                        res["id"], "rejected", user["id"]
                                    )
                                    st.success("Rejected.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error rejecting: {e}")

                    elif res["status"] == "approved":
                        if st.button(
                            "Cancel Approval",
                            key=f"cancel_approval_{res['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.update_reservation_status(res["id"], "pending", None)
                                st.success("Approval cancelled.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error cancelling: {e}")

                    # Delete button (master only)
                    if is_master:
                        if st.button(
                            "Delete",
                            key=f"delete_{res['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            confirm_delete = st.checkbox(
                                "I understand this cannot be undone",
                                key=f"confirm_delete_{res['id']}",
                            )
                            if confirm_delete:
                                try:
                                    db.delete_reservation(res["id"])
                                    st.success("Deleted.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {e}")

                    # Add to blacklist button
                    if not res.get("is_blacklisted"):
                        if st.button(
                            "Add to Blacklist",
                            key=f"blacklist_{res['id']}",
                            use_container_width=True,
                        ):
                            reason = st.text_input(
                                "Blacklist Reason", key=f"reason_{res['id']}"
                            )
                            if st.button(
                                "Confirm Add",
                                key=f"add_blacklist_{res['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    db.add_to_blacklist(
                                        commander_id=res["commander_id"],
                                        nickname=res["nickname"],
                                        reason=reason if reason else "Added by admin",
                                        added_by=user["id"],
                                    )
                                    st.success("Added to blacklist.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error adding: {e}")

    else:
        st.info("No reservations to display.")

    st.markdown("---")

    # Guide message
    st.markdown("""
    ### Admin Guide

    - **Pending**: Can approve or reject
    - **Approved**: Can cancel approval
    - **Rejected/Cancelled**: Cannot change status
    - **Blacklist**: Automatically displayed

    Only master accounts can delete reservations.
    """)
