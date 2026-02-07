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

    # user가 None인 경우 처리
    if not user:
        st.error("User information not found. Please log in again.")
        return

    # Blacklist check
    commander_number = user.get("commander_number", "")
    if commander_number:
        blacklisted = db.check_blacklist(commander_number)

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
        # User info display - show saved server/alliance from registration
        st.markdown("### User Info")
        st.info(f"""
        - **Nickname**: {user.get("nickname", "Unknown")}
        - **Commander ID**: {user.get("commander_number", "N/A")}
        - **Server**: {user.get("server", "N/A")} (saved from registration)
        - **Alliance**: {user.get("alliance", "N/A") if user.get("alliance") else "None"} (saved from registration)
        """)

        st.markdown("---")

        # Reservation form - server/alliance pre-filled from registration
        st.markdown("### Reservation Info")

        # Server input - pre-filled from registration but editable
        server = st.text_input(
            "Server",
            value=user.get("server", ""),
            placeholder="e.g., #095 woLF",
            help="Pre-filled from your registration info",
        )

        # Alliance (optional) - pre-filled from registration but editable
        alliance = st.text_input(
            "Alliance",
            value=user.get("alliance", ""),
            placeholder="Enter your alliance if any",
            help="Pre-filled from your registration info",
        )

        # Current participant count
        participants = db.list_participants()
        participants_count = len([p for p in participants if p.get("completed")])

        # Approved reservations count
        all_reservations = db.list_reservations()
        approved_count = len(all_reservations)

        total_count = participants_count + approved_count

        st.info(f"Current Members: {total_count} / {db.MAX_PARTICIPANTS}")

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
                    # 서버가 비어 있으면 회원가입 시 저장된 값 사용
                    reservation_server = server if server else user.get("server", "")

                    reservation_id = db.create_reservation(
                        user_id=user["id"],
                        nickname=user.get("nickname", ""),
                        commander_number=user.get("commander_number", ""),
                        server=reservation_server,
                        notes=notes if notes else None,
                    )

                    # Reservation submitted
                    if reservation_id > 0:
                        st.success(
                            f"Reservation submitted! (Reservation ID: {reservation_id})"
                        )
                    else:
                        st.error(
                            "Failed to create reservation. You may be blacklisted or capacity is full."
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
                st.markdown(f"""
                **{res["created_at"]}**
                - Server: {res.get("server", "N/A")}
                - Alliance: {res.get("alliance", "N/A") if res.get("alliance") else "None"}
                """)

                if res.get("notes"):
                    st.text(f"Notes: {res['notes']}")

                st.markdown("---")
        else:
            st.info("No reservation history yet.")
