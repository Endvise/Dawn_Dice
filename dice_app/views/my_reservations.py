#!/usr/bin/env python3
"""
My Reservations page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show my reservations page"""
    auth.require_login()

    user = auth.get_current_user()

    st.title("My Reservations")
    st.markdown("---")

    # Statistics
    my_reservations = db.list_reservations(user_id=user["id"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", len(my_reservations))

    with col2:
        pending = len([r for r in my_reservations if r["status"] == "pending"])
        st.metric("Pending", pending)

    with col3:
        approved = len([r for r in my_reservations if r["status"] == "approved"])
        st.metric("Approved", approved)

    with col4:
        rejected = len([r for r in my_reservations if r["status"] == "rejected"])
        st.metric("Rejected", rejected)

    st.markdown("---")

    # Filter
    st.markdown("### Filter")

    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "Status Filter",
            ["All", "Pending", "Approved", "Rejected", "Cancelled"],
            key="status_filter",
        )

    with col2:
        blacklist_filter = st.selectbox(
            "Blacklist Filter", ["All", "Blacklisted", "Normal"], key="blacklist_filter"
        )

    st.markdown("---")

    # Reservation list
    filtered_reservations = []

    for res in my_reservations:
        # Waitlist info
        waitlist_info = ""
        if res.get("status") == "waitlisted":
            waitlist_order = res.get("waitlist_order")
            waitlist_position = res.get("waitlist_position")
            waitlist_info = (
                f" (Waitlist: #{waitlist_order} / Current: #{waitlist_position})"
            )

        status_color = {
            "pending": "🟡 PENDING",
            "approved": "🟢 APPROVED",
            "rejected": "🔴 REJECTED",
            "cancelled": "⚪ CANCELLED",
            "waitlisted": "🔵 WAITLISTED",
        }
        status_label = status_color.get(res["status"], res["status"].upper())

        # Reservation card
        with st.expander(
            f"{status_label}{waitlist_info} - {res['created_at'][:19]} (ID: {res['id']})"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Nickname**: {res["nickname"]}
                **Commander ID**: {res["commander_id"]}
                **Server**: {res["server"]}
                **Alliance**: {res["alliance"] if res["alliance"] else "None"}
                **Applied At**: {res["created_at"]}
                **Status**: {res["status"]}
                """)

                if res.get("approved_at"):
                    st.markdown(f"**Approved At**: {res['approved_at']}")

                if res.get("waitlist_order"):
                    st.info(f"🔵 Waitlist Number: {res.get('waitlist_order')}")

                if res.get("notes"):
                    st.text(f"**Notes**: {res['notes']}")

                if res.get("is_blacklisted"):
                    st.warning(f"⚠️ **Blacklist**: {res.get('blacklist_reason', 'N/A')}")

            with col2:
                # Cancel button (only when pending)
                if res["status"] == "pending":
                    if st.button(
                        "Cancel",
                        key=f"cancel_{res['id']}",
                        use_container_width=True,
                    ):
                        try:
                            db.cancel_reservation(res["id"])
                            st.success("Reservation cancelled.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error cancelling: {e}")

                # Approver info
                if res.get("approved_by"):
                    approver = db.get_user_by_id(res["approved_by"])
                    if approver:
                        st.info(
                            f"Approved by: {approver.get('nickname', approver.get('username', 'Unknown'))}"
                        )

    else:
        st.info("No reservations to display.")

    st.markdown("---")

    # Guide message
    st.markdown("""
    ### Guide

    - **Pending**: Waiting for admin approval
    - **Approved**: Reservation approved
    - **Rejected**: Rejected by admin
    - **Cancelled**: Cancelled by user

    Commander IDs on the blacklist cannot make reservations.
    """)
