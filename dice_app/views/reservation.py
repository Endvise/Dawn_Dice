#!/usr/bin/env python3
"""
Reservation page
"""

import streamlit as st
import database as db
import auth
from database import execute_query


def show():
    """Show reservation page"""
    auth.require_login()

    user = auth.get_current_user()

    # Blacklist check
    if user.get("commander_id"):
        blacklisted = db.check_blacklist(user["commander_id"])

        if blacklisted:
            st.error(
                f"You are on the blacklist. (Reason: {blacklisted.get('reason', 'N/A')})"
            )
            st.info("Please contact the administrator.")
            return

    st.title("Make Reservation")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # User info display
        st.markdown("### User Info")
        st.info(f"""
        - **Nickname**: {user.get("nickname", "Unknown")}
        - **Commander ID**: {user.get("commander_id", "N/A")}
        - **Server**: {user.get("server", "N/A")}
        - **Alliance**: {user.get("alliance", "N/A") if user.get("alliance") else "None"}
        """)

        st.markdown("---")

        # Reservation form
        st.markdown("### Reservation Info")

        # Server input
        server = st.text_input(
            "Server", value=user.get("server", ""), placeholder="e.g., #095 woLF"
        )

        # Alliance (optional)
        alliance = st.text_input(
            "Alliance",
            value=user.get("alliance", ""),
            placeholder="Enter your alliance if any",
        )

        # Current participant count
        result = execute_query(
            "SELECT COUNT(*) as count FROM participants WHERE completed = 1",
            fetch="one",
        )
        participants_count = result.get("count", 0) if result else 0

        result = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
            fetch="one",
        )
        approved_count = result.get("count", 0) if result else 0

        total_count = participants_count + approved_count

        st.info(f"Current participants: {total_count} / {db.MAX_PARTICIPANTS}")

        if total_count >= db.MAX_PARTICIPANTS:
            st.warning("Capacity full. Reservations will be added to waiting list.")

        # Notes
        notes = st.text_area(
            "Notes", placeholder="Add any additional information", height=100
        )

        st.markdown("---")

        # Button area
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

        with col_btn2:
            if st.button(
                "Submit Reservation", use_container_width=True, type="primary"
            ):
                try:
                    reservation_id = db.create_reservation(
                        user_id=user["id"],
                        nickname=user.get("nickname", ""),
                        commander_id=user.get("commander_id", ""),
                        server=server,
                        alliance=alliance if alliance else None,
                        notes=notes if notes else None,
                    )

                    # Blacklist warning
                    reservation = db.get_reservation_by_id(reservation_id)

                    if reservation and reservation.get("status") == "waitlisted":
                        waitlist_order = reservation.get("waitlist_order")
                        st.warning(
                            f"Added to waiting list. Waitlist number: {waitlist_order}"
                        )
                    elif reservation and reservation.get("status") == "pending":
                        st.success(
                            f"Reservation submitted! (Reservation ID: {reservation_id})"
                        )

                    if reservation and reservation.get("is_blacklisted"):
                        st.warning(
                            f"Your Commander ID is on the blacklist. (Reason: {reservation.get('blacklist_reason', 'N/A')})"
                        )

                except Exception as e:
                    st.error(f"Error during reservation: {e}")

        # Guide message
        st.markdown("---")
        st.markdown("""
        ### Reservation Guide

        - Reservations require admin approval.
        - Commander IDs on the blacklist cannot make reservations.
        - Check reservation status on "My Reservations" page.
        - Server/Alliance saved at time of reservation.
        """)

        # Recent reservations preview
        st.markdown("---")
        st.markdown("### Recent Reservations")

        my_reservations = db.list_reservations(user_id=user["id"], limit=5)

        if my_reservations:
            for res in my_reservations:
                status_color = {
                    "pending": "🟡",
                    "approved": "🟢",
                    "rejected": "🔴",
                    "cancelled": "⚪",
                }

                status_label = (
                    status_color.get(res["status"], "❓") + " " + res["status"].upper()
                )

                st.markdown(f"""
                **{status_label}** - {res["created_at"]}
                - Server: {res["server"]}
                - Alliance: {res["alliance"] if res["alliance"] else "None"}
                """)

                if res.get("is_blacklisted"):
                    st.warning(f"Blacklist: {res.get('blacklist_reason', 'N/A')}")

                if res.get("notes"):
                    st.text(f"Notes: {res['notes']}")

                st.markdown("---")
        else:
            st.info("No reservation history yet.")
