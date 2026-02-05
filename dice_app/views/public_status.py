#!/usr/bin/env python3
"""
Public Reservation Status Page
Reservation status page accessible to non-logged-in users
"""

import streamlit as st
import database as db
from datetime import datetime


def show_public_status():
    """Display public reservation status."""
    st.set_page_config(
        page_title="Reservation Status - DaWn Dice Party",
        page_icon="🎲",
        layout="centered",
    )

    st.title("🎲 DaWn Dice Party - Reservation Status")

    # Get active session info
    session = db.get_active_session()
    if not session:
        st.info("No active reservation session at this time.")
        st.markdown("""
        ---
        **Reservation Information**
        - Please check announcements for reservation open time.
        - When reservations open, this page will be updated immediately.
        """)
        return

    # Display session info
    session_name = session.get(
        "session_name", f"Session {session.get('session_number', 1)}"
    )
    session_date = session.get("session_date", "")

    st.markdown(f"### {session_name}")
    if session_date:
        st.markdown(f"**Date:** {session_date}")

    st.markdown("---")

    # Check if reservation is open
    is_open = session.get("is_reservation_open", False)
    open_time = session.get("reservation_open_time", "")
    close_time = session.get("reservation_close_time", "")

    if not is_open:
        st.warning("Reservations are currently CLOSED.")
        if open_time:
            st.info(f"**Reservation Opens:** {open_time}")
        if close_time:
            st.info(f"**Reservation Closes:** {close_time}")
        return

    # Reservation is open
    st.success("Reservations are OPEN!")

    # Statistics
    approved_count = db.get_approved_reservation_count(session.get("id", ""))
    max_participants = session.get("max_participants", 180)
    remaining = max_participants - approved_count

    # Progress and status
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Reservations", f"{approved_count} / {max_participants}")

    with col2:
        if remaining > 0:
            st.metric("Remaining Spots", f"{remaining}", delta_color="normal")
        else:
            st.metric("Remaining Spots", "0", delta="Full", delta_color="inverse")

    with col3:
        waitlist_count = 0  # Waitlist system not available in simplified schema
        st.metric("Waitlist", f"{waitlist_count}")

    # Progress bar
    progress = min(approved_count / max_participants, 1.0)
    st.progress(progress)

    # Status message
    st.markdown("---")
    if remaining > 0:
        st.info(f"Reservations are available! {remaining} spots remaining.")
    else:
        st.error(
            "Capacity reached! Only waitlist registration is available. "
            "Waitlist spots are determined on a first-come, first-served basis."
        )

    # How to reserve
    st.markdown("""
    ---
    ### How to Reserve

    1. Click **Sign Up** to register with your Commander ID
    2. Log in and go to **Make Reservation**
    3. Submit your reservation request
    4. Confirmation will be sent upon approval
    """)


if __name__ == "__main__":
    show_public_status()
