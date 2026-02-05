#!/usr/bin/env python3
"""
Admin Reservation Settings Page
"""

import streamlit as st
import database as db
from datetime import datetime


def show_reservation_settings():
    """Reservation Settings Admin Page."""
    st.title("Reservation Settings")

    # Get active session
    session = db.get_active_session()
    if not session:
        st.warning("No active session found.")

        with st.expander("Create New Session"):
            st.info(
                "Please create a new session from the Event Sessions Management page."
            )

        return

    session_id = session.get("id", "")
    session_name = session.get(
        "session_name", f"Session {session.get('session_number', 1)}"
    )

    # Reservation status management
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Reservation Status")
        is_open = session.get("is_reservation_open", False)

        if is_open:
            st.success("Reservations are OPEN")
            if st.button("Close Reservations", type="primary"):
                db.update_session_active(session_id, False)
                st.rerun()
        else:
            st.error("Reservations are CLOSED")
            if st.button("Open Reservations", type="primary"):
                db.update_session_active(session_id, True)
                st.rerun()

    with col2:
        st.subheader("Reservation Time Settings")

        # Time input
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            open_time = st.text_input(
                "Reservation Open Time",
                value=session.get("reservation_open_time", "") or "",
                placeholder="YYYY-MM-DD HH:MM",
                help="Example: 2026-02-15 12:00",
            )
        with col_time2:
            close_time = st.text_input(
                "Reservation Close Time",
                value=session.get("reservation_close_time", "") or "",
                placeholder="YYYY-MM-DD HH:MM",
                help="Example: 2026-02-20 23:59",
            )

        if st.button("Save Times"):
            try:
                db.update(
                    session_id,
                    {
                        "reservation_open_time": open_time,
                        "reservation_close_time": close_time,
                    },
                    {"id": f"eq.{session_id}"},
                )
                st.success("Times saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save: {e}")

    st.markdown("---")

    # Current reservation status
    st.subheader("Current Reservation Status")

    # Calculate statistics
    approved_count = db.get_approved_reservation_count(session_id)
    pending_count = 0  # No status field in simplified schema
    waitlisted_count = 0  # Waitlist not available
    rejected_count = 0  # No status field in simplified schema
    max_participants = session.get("max_participants", 180)

    # Statistics cards
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    col_stat1.metric(
        "Approved",
        approved_count,
        f"{max_participants - approved_count} remaining",
        delta_color="normal",
    )
    col_stat2.metric("Pending", pending_count)
    col_stat3.metric("Waitlist", waitlisted_count)
    col_stat4.metric("Rejected", rejected_count)
    col_stat5.metric("Capacity", f"{approved_count}/{max_participants}")

    # Progress bar
    progress = min(approved_count / max_participants, 1.0)
    st.progress(progress)

    # Status messages
    if approved_count >= max_participants:
        st.error(
            "Capacity exceeded! Additional reservations will be added to waitlist."
        )
    elif approved_count >= max_participants * 0.9:
        st.warning("Almost at capacity!")
    else:
        st.success("Reservations are proceeding smoothly.")

    # Public view settings
    st.markdown("---")
    st.subheader("Public Status Page Settings")

    # Enable public view
    enable_public_view = st.checkbox(
        "Show reservation status to public",
        value=session.get("enable_public_view", False),
        help="When checked, non-logged-in users can view the reservation status.",
    )

    if st.button("Save Settings"):
        try:
            db.update(
                session_id,
                {"enable_public_view": enable_public_view},
                {"id": f"eq.{session_id}"},
            )
            st.success("Settings saved!")
        except Exception as e:
            st.error(f"Failed to save settings: {e}")

    # Public status page link
    if enable_public_view:
        st.info(
            "Public status page is enabled. Users can access it via the public status URL."
        )


def show_reservation_list():
    """Show reservation list with filters."""
    st.title("Reservation List Management")

    # Filter
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("Search by Commander ID or Nickname")

    # Get reservations
    reservations = db.list_reservations()

    # Apply search
    if search:
        reservations = [
            r
            for r in reservations
            if search in str(r.get("commander_number", ""))
            or search in str(r.get("nickname", ""))
        ]

    # Display results
    st.write(f"**Total: {len(reservations)}**")

    if reservations:
        # Table display
        import pandas as pd

        df = pd.DataFrame(reservations)

        # Select columns to display
        display_cols = [
            "nickname",
            "commander_number",
            "server",
            "created_at",
            "reserved_at",
        ]
        st.dataframe(df[display_cols], use_container_width=True)

        # Detail actions
        with st.expander("Actions"):
            selected = st.selectbox(
                "Select Reservation",
                [f"{r['nickname']} ({r['commander_number']})" for r in reservations],
            )
            if selected:
                idx = [
                    f"{r['nickname']} ({r['commander_number']})" for r in reservations
                ].index(selected)
                res = reservations[idx]

                st.write("### Selected Reservation Details")
                st.json(res)

                # Delete button
                if st.button("Cancel/Delete Reservation"):
                    db.cancel_reservation(res["id"])
                    st.success("Reservation cancelled.")
                    st.rerun()


if __name__ == "__main__":
    tab1, tab2 = st.tabs(["Settings", "Reservation List"])
    with tab1:
        show_reservation_settings()
    with tab2:
        show_reservation_list()
