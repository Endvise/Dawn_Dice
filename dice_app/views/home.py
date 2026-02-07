#!/usr/bin/env python3
"""
Main Homepage - Session-based Reservation System
"""

import streamlit as st
import database as db
import auth
import utils
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def get_reservation_status() -> Dict[str, Any]:
    """Returns reservation status."""
    # Get current active session first
    active_session = db.get_active_session()
    current_session_name = (
        active_session.get("session_name") if active_session else None
    )

    # Get participants and reservations filtered by current session
    participants = (
        db.list_participants(current_session_name) if current_session_name else []
    )
    reservations = (
        db.list_reservations(event_name=current_session_name)
        if current_session_name
        else []
    )

    # Existing participants count
    participants_count = len(participants)

    # Approved reservations count
    approved_count = len(reservations)

    # Total participants for current session
    total_count = participants_count + approved_count

    if active_session:
        session_id = active_session.get("id")
        session_name = active_session.get("session_name", "")
        session_number = active_session.get("session_number", "")
        max_participants = active_session.get("max_participants", db.MAX_PARTICIPANTS)
        reservation_open_time = active_session.get("reservation_open_time")
        reservation_close_time = active_session.get("reservation_close_time")
        session_date = active_session.get("session_date")

        # Calculate session counts (already filtered by session)
        session_participants = len(participants)
        session_reservations = len(reservations)
        session_total = session_participants + session_reservations

        # Remaining spots for waitlist
        remaining_spots = max(0, max_participants - session_total)

        # Check if reservation is open
        now = datetime.now()
        is_reservation_open = True
        is_reservation_closed = False

        if reservation_open_time:
            try:
                open_time = datetime.fromisoformat(
                    reservation_open_time.replace("Z", "+00:00")
                )
                if now < open_time:
                    is_reservation_open = False
            except (ValueError, TypeError):
                pass

        if reservation_close_time:
            try:
                close_time = datetime.fromisoformat(
                    reservation_close_time.replace("Z", "+00:00")
                )
                if now >= close_time:
                    is_reservation_closed = True
                    is_reservation_open = False
            except (ValueError, TypeError):
                pass

        return {
            "total": session_total,
            "max": max_participants,
            "approved": approved_count,
            "is_full": session_total >= max_participants,
            "session_number": session_number,
            "session_name": session_name,
            "session_date": session_date,
            "reservation_open_time": reservation_open_time,
            "reservation_close_time": reservation_close_time,
            "is_reservation_open": is_reservation_open,
            "is_reservation_closed": is_reservation_closed,
            "is_session_active": True,
            "overall_total": total_count,
            "overall_max": db.MAX_PARTICIPANTS,
            "overall_is_full": total_count >= db.MAX_PARTICIPANTS,
            "remaining_spots": remaining_spots,
        }
    else:
        return {
            "total": total_count,
            "max": db.MAX_PARTICIPANTS,
            "approved": approved_count,
            "is_full": total_count >= db.MAX_PARTICIPANTS,
            "session_number": None,
            "session_name": None,
            "session_date": None,
            "reservation_open_time": None,
            "reservation_close_time": None,
            "is_reservation_open": False,  # No session = reservations not open
            "is_reservation_closed": True,
            "is_session_active": False,
            "overall_total": total_count,
            "overall_max": db.MAX_PARTICIPANTS,
            "overall_is_full": total_count >= db.MAX_PARTICIPANTS,
            "remaining_spots": max(0, db.MAX_PARTICIPANTS - total_count),
        }


def get_time_remaining(open_time_str: str) -> Dict[str, int]:
    """Returns time remaining until open time."""
    try:
        open_time = datetime.fromisoformat(open_time_str.replace("Z", "+00:00"))
        now = datetime.now()
        diff = open_time - now

        if diff.total_seconds() <= 0:
            return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}

        total_seconds = int(diff.total_seconds())
        days = total_seconds // (24 * 3600)
        hours = (total_seconds % (24 * 3600)) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds}
    except (ValueError, TypeError):
        return {"days": 0, "hours": 0, "minutes": 0, "seconds": 0}


def format_datetime(dt_str: str, show_timezone: bool = True) -> str:
    """Format datetime string for display with user's timezone."""
    if not dt_str:
        return "N/A"
    timezone_key = "timezone_selector"
    tz = st.session_state.get(f"selected_{timezone_key}", "UTC")
    formatted = utils.format_utc_to_timezone(dt_str, tz)
    if show_timezone:
        display_name = utils.get_timezone_display_name(tz)
        return f"{formatted} ({display_name})"
    return formatted


def format_datetime_utc(dt_str: str) -> str:
    """Format datetime string for display in UTC."""
    if not dt_str:
        return "N/A"
    try:
        dt = utils.parse_utc_time(dt_str)
        if dt:
            return dt.strftime("%Y-%m-%d %H:%M")
        return str(dt_str)
    except (ValueError, TypeError):
        return str(dt_str)


def show():
    """Display main page"""
    st.set_page_config(
        page_title="DaWn Dice Party",
        page_icon="🎲",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Session initialization
    auth.init_session_state()

    # Developer tools prevention (except admin)
    import security_utils

    security_utils.inject_devtools_block()

    # Home page
    st.title("🎲 DaWn Dice Party")
    st.markdown("---")

    # Get reservation status
    status = get_reservation_status()

    # Display session info prominently
    if status["is_session_active"]:
        session_number = status["session_number"]
        session_name = status["session_name"]
        session_date = status["session_date"]

        # Prominent session header
        if session_number:
            st.markdown(f"## 🎯 Session {session_number}")
        if session_name:
            st.markdown(f"### 📅 {session_name}")

        # Reservation status display
        if status["is_reservation_closed"]:
            st.error("## ⛔ Reservations Closed")
        elif status["is_reservation_open"]:
            if status["is_full"]:
                st.warning("## ⏳ Waitlist Only")
            else:
                st.success("## ✅ Reservations Open")
        else:
            st.info("## ⏰ Reservations Opening Soon")

        # Time information
        st.markdown("#### 🕐 Reservation Times")
        st.caption("Times shown in your local timezone")

        col_time1, col_time2 = st.columns(2)

        with col_time1:
            if status["reservation_open_time"]:
                st.info(
                    f"📅 **Reservation Opens**: {format_datetime(status['reservation_open_time'])}"
                )
            else:
                st.info("📅 **Reservation Opens**: Immediate")

        with col_time2:
            if status["reservation_close_time"]:
                st.info(
                    f"⏰ **Reservation Closes**: {format_datetime(status['reservation_close_time'])}"
                )
            else:
                st.info("⏰ **Reservation Closes**: When Full")

        # Show UTC reference
        if status["reservation_open_time"] or status["reservation_close_time"]:
            with st.expander("📌 UTC Reference Times"):
                if status["reservation_open_time"]:
                    st.text(
                        f"Opens: {format_datetime_utc(status['reservation_open_time'])} UTC"
                    )
                if status["reservation_close_time"]:
                    st.text(
                        f"Closes: {format_datetime_utc(status['reservation_close_time'])} UTC"
                    )
    else:
        # No active session
        st.warning("## 📢 No Active Session")
        st.info("Reservations are not available at this time.")
        st.markdown(
            "Please wait for an administrator to create and activate a session."
        )
        st.markdown("---")

    # Overall statistics section (shown regardless of session status)
    st.markdown("---")

    # Overall statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Current Members",
            f"{status['overall_total']} / {status['overall_max']}",
        )

    with col2:
        st.metric("Approved Reservations", f"{status['approved']}")

    with col3:
        st.metric(
            "Spots Remaining", f"{status['overall_max'] - status['overall_total']}"
        )

    st.markdown("---")

    # Login-based messages
    if auth.is_authenticated():
        user = auth.get_current_user()

        st.markdown("### 👤 Welcome!")

        # Blacklist check
        if user:
            commander_number = user.get("commander_number") or user.get("username")
            if commander_number:
                blacklisted = db.check_blacklist(commander_number)

                if blacklisted:
                    st.error("⛔ You are on the blacklist.")
                    st.info("Please contact the administrator.")
                    return

        # User info display
        if user:
            st.markdown(f"""
            - **Nickname**: {user.get("nickname", "Unknown")}
            - **Commander ID**: {user.get("commander_number", "N/A")}
            - **Server**: {user.get("server", "N/A")}
            - **Alliance**: {user.get("alliance", "None") if user.get("alliance") else "None"}
            """)

        # My reservations status
        my_reservations = []
        if user:
            my_reservations = db.list_reservations(user_id=user["id"])

            if my_reservations:
                latest_reservation = my_reservations[0]

                st.markdown("---")
                st.markdown("### 📊 My Reservation Status")

                st.success(f"🎉 Your reservation is confirmed!")

                st.markdown(
                    f"**Reservation Date**: {latest_reservation.get('created_at', 'N/A')}"
                )

                # Queue position info
                st.markdown("---")
                st.markdown("### ⏰ Queue Position")

                total = status["total"]
                max_capacity = status["max"]

                if total < max_capacity:
                    st.success(f"You are #{total} in queue (within capacity)")
                else:
                    position = total - max_capacity + 1
                    st.warning(f"You are #{total} in queue (waitlist #{position})")

            # New reservation guide
        if not my_reservations:
            st.info("No reservation yet.")
            st.markdown("---")

            # Show reservation button only if reservation is open
            if user and status["is_session_active"]:
                if status["is_reservation_open"]:
                    if not status["is_full"]:
                        st.markdown("### 📝 Make Reservation")
                        st.info("Click the button below to make your reservation!")
                    else:
                        st.warning(
                            "⚠️ Current session is full. Only waitlist registration available."
                        )
                    if st.button(
                        "Go to Reservation",
                        use_container_width=True,
                        type="primary",
                        key=f"home_go_to_reservation_{user['id']}"
                        if user
                        else "home_go_to_reservation",
                    ):
                        st.session_state["page"] = "📝 Make Reservation"
                        st.rerun()
                elif status["is_reservation_closed"]:
                    st.error("⛔ Reservations are closed.")
                else:
                    # Reservation not yet open
                    st.warning("⏰ Reservations are not open yet.")
                    if status["reservation_open_time"]:
                        st.info(
                            f"📅 Reservations open at: {format_datetime(status['reservation_open_time'])}"
                        )
            elif user and not status["is_session_active"]:
                st.markdown("### 📝 Make Reservation")
                st.warning("📢 No active session. Reservations are not available.")
                st.info("Please wait for an admin to create and activate a session.")

                if st.button(
                    "Go to Reservation",
                    use_container_width=True,
                    type="primary",
                    key=f"home_go_to_reservation_{user['id']}"
                    if user
                    else "home_go_to_reservation",
                ):
                    st.session_state["page"] = "📝 Make Reservation"
                    st.rerun()

    else:
        st.markdown("### 👋 Welcome!")
        st.markdown("Welcome to DaWn Dice Party!")
        st.markdown("---")

        # Login button area (left aligned)
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("### 📝 Login")

            # Login form
            with st.form("login_form"):
                username = st.text_input(
                    "Commander ID or Username", key="home_login_username"
                )
                password = st.text_input(
                    "Password", type="password", key="home_login_password"
                )

                submitted = st.form_submit_button(
                    "Login", use_container_width=True, type="primary"
                )

                if submitted:
                    success, message = auth.login(username, password)

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            # Sign Up button (outside form)
            if st.button("Sign Up", use_container_width=True, key="home_register"):
                st.session_state["show_register"] = True
                st.rerun()

        st.markdown("---")

        # Main information
        st.markdown("### 📋 Information")

        st.markdown("""
        - **First-come, first-served**: First to reserve gets priority
        - **Maximum participants**: 180 per session
        - **Waitlist system**: Auto waitlist when capacity exceeded
        - **Commander ID**: 10-digit number
        - **Password**: Minimum 8 characters

        ## Session-based System

        - When full, auto switch to waitlist
        - Previous participants get priority
        - New participants join new sessions
        - Shows 'Waitlist Only' when full

        ## Priority System

        **1st Priority**: Previous participants
        - Within capacity: Reserve in order

        **2nd Priority**: First-come reservation
        - Reserve in order

        ## When Full

        - Shows 'Waitlist Only' message
        - Waitlist number assigned by order
        """)

        st.markdown("---")

        # Announcements display
        st.markdown("### 📢 Announcements")

        # Latest announcements display (maximum 5, pinned first)
        announcements = db.list_announcements(is_active=True, limit=5)

        # Pinned announcements first
        pinned = [a for a in announcements if a.get("is_pinned")]
        regular = [a for a in announcements if not a.get("is_pinned")]

        display_announcements = (pinned + regular[:3]) if regular else pinned

        if display_announcements:
            for ann in display_announcements:
                # Category badge
                category_badge = {
                    "notice": "📢",
                    "guide": "ℹ️",
                    "event": "🎉",
                }

                badge = category_badge.get(ann.get("category", "notice"), "📢")

                # Pinned indicator
                pin_indicator = " 📌 Pinned" if ann.get("is_pinned") else ""

                with st.expander(f"{badge} {ann['title']}{pin_indicator}"):
                    st.markdown(ann["content"])

                    st.markdown(
                        f"Author: {ann.get('author_name', 'Unknown')} | Date: {ann.get('created_at', 'N/A')}"
                    )
        else:
            st.info("No announcements yet.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>©2026 DaWn Dice Party</div>",
        unsafe_allow_html=True,
    )

    # Admin-only messages
    if auth.is_admin():
        st.markdown("---")
        st.info("Admin Menu")

        # Admin dashboard link
        st.markdown("[📊 Go to Dashboard")

        # Admin announcements link
        st.markdown("[📢 Go to Announcements")

        # Admin event sessions link
        st.markdown("[🎲 Go to Event Sessions")
