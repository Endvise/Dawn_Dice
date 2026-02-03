#!/usr/bin/env python3
"""
Main Homepage - Session-based Reservation System
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def get_reservation_status() -> Dict[str, Any]:
    """Returns reservation status."""
    # Existing participants count
    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    )
    participants_count = result["count"] if result else 0

    # Approved reservations count
    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    approved_count = result["count"] if result else 0

    # Total participants
    total_count = participants_count + approved_count

    # Get current active session
    active_session = get_active_session()

    if active_session:
        # Session participants count
        session_id = active_session["id"]
        session_name = active_session.get("session_name", "")
        session_number = active_session.get("session_number", "")
        max_participants = active_session.get("max_participants", db.MAX_PARTICIPANTS)
        reservation_open_time = active_session.get("reservation_open_time")
        reservation_close_time = active_session.get("reservation_close_time")

        # Session approved reservations count
        result = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE event_name = ? AND status = 'approved'",
            (session_name,),
            fetch="one",
        )
        session_approved_count = result["count"] if result else 0

        # Total session participants (existing + approved)
        result = execute_query(
            "SELECT COUNT(*) as count FROM participants WHERE event_name = ? AND completed = 1",
            (session_name,),
            fetch="one",
        )
        session_total_count = result["count"] if result else 0

        session_count = session_total_count + session_approved_count

        result_waitlist = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE status = 'waitlisted'",
            fetch="one",
        )
        waitlist_count = result_waitlist["count"] if result_waitlist else 0

        # Check if reservation is open
        now = datetime.now()
        is_reservation_open = True
        is_reservation_closed = False

        if reservation_open_time:
            try:
                open_time = datetime.strptime(
                    reservation_open_time, "%Y-%m-%d %H:%M:%S"
                )
                if now < open_time:
                    is_reservation_open = False
            except (ValueError, TypeError):
                pass

        if reservation_close_time:
            try:
                close_time = datetime.strptime(
                    reservation_close_time, "%Y-%m-%d %H:%M:%S"
                )
                if now >= close_time:
                    is_reservation_closed = True
                    is_reservation_open = False
            except (ValueError, TypeError):
                pass

        return {
            "total": session_count,
            "max": max_participants,
            "approved": session_approved_count,
            "is_full": session_count >= max_participants,
            "session_number": session_number,
            "session_name": session_name,
            "session_date": active_session.get("session_date"),
            "reservation_open_time": reservation_open_time,
            "reservation_close_time": reservation_close_time,
            "is_reservation_open": is_reservation_open,
            "is_reservation_closed": is_reservation_closed,
            "is_session_active": True,
            "overall_total": total_count,
            "overall_max": db.MAX_PARTICIPANTS,
            "overall_is_full": total_count >= db.MAX_PARTICIPANTS,
            "overall_waitlist": waitlist_count,
        }
    else:
        result_waitlist = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE status = 'waitlisted'",
            fetch="one",
        )
        waitlist_count = result_waitlist["count"] if result_waitlist else 0

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
            "is_reservation_open": False,
            "is_reservation_closed": False,
            "is_session_active": False,
            "overall_total": total_count,
            "overall_max": db.MAX_PARTICIPANTS,
            "overall_is_full": total_count >= db.MAX_PARTICIPANTS,
            "overall_waitlist": waitlist_count,
        }


def get_active_session() -> Optional[Dict[str, Any]]:
    """Returns the active session."""
    result = execute_query(
        """
        SELECT s.*, u.nickname as creator_name
        FROM event_sessions s
        LEFT JOIN users u ON s.created_by = u.id
        WHERE s.is_active = 1
        LIMIT 1
        """,
        fetch="one",
    )
    return dict(result) if result else None


def get_my_order(user_id: int) -> tuple[Optional[int], bool]:
    """Returns user's order (order number, within capacity)."""
    # Existing participants count
    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    )
    participants_count = result["count"] if result else 0

    # Approved reservations count
    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    approved_count = result["count"] if result else 0

    # My reservation
    my_reservations = execute_query(
        "SELECT * FROM reservations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
        fetch="one",
    )

    if not my_reservations:
        return None, False

    # Calculate order position
    total_before_me = participants_count + approved_count

    if my_reservations["status"] == "approved":
        my_order = total_before_me
    elif my_reservations["status"] in ["pending", "waitlisted"]:
        my_order = total_before_me + 1
    else:
        my_order = total_before_me

    return my_order, my_order <= db.MAX_PARTICIPANTS


def get_time_remaining(open_time_str: str) -> Dict[str, int]:
    """Returns time remaining until open time."""
    try:
        open_time = datetime.strptime(open_time_str, "%Y-%m-%d %H:%M:%S")
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
    st.markdown("by Entity")
    st.markdown("---")

    # Get reservation status
    status = get_reservation_status()

    # Display session info prominently
    if status["is_session_active"]:
        session_number = status["session_number"]
        session_name = status["session_name"]

        # Prominent session header
        if session_number:
            st.markdown(f"## 🎯 This is the {session_number} Session")
        if session_name:
            st.markdown(f"### 📅 {session_name}")

        # Reservation status display
        if status["is_reservation_closed"]:
            st.error("## ⛔ Reservation Closed")
        elif status["is_reservation_open"]:
            st.success("## ✅ Reservation Open")
        else:
            st.warning("## ⏰ Reservation Opening Soon")

        # Countdown timer if reservation is not yet open
        if (
            status["reservation_open_time"]
            and not status["is_reservation_open"]
            and not status["is_reservation_closed"]
        ):
            time_remaining = get_time_remaining(status["reservation_open_time"])
            if (
                time_remaining["days"] > 0
                or time_remaining["hours"] > 0
                or time_remaining["minutes"] > 0
                or time_remaining["seconds"] > 0
            ):
                col_cd1, col_cd2, col_cd3, col_cd4 = st.columns(4)
                with col_cd1:
                    st.metric("Days", time_remaining["days"])
                with col_cd2:
                    st.metric("Hours", time_remaining["hours"])
                with col_cd3:
                    st.metric("Minutes", time_remaining["minutes"])
                with col_cd4:
                    st.metric("Seconds", time_remaining["seconds"])
                st.info(f"📅 Reservation opens at: {status['reservation_open_time']}")

        # Capacity info
        if status["is_reservation_open"]:
            if status["is_full"]:
                st.error(
                    f"⛔ Capacity Full - Only Waitlist Registration Available ({status['total']} / {status['max']}, Waitlist: {status['overall_waitlist']})"
                )
            else:
                st.info(
                    f"📊 {status['total']} / {status['max']} participants (Waitlist: {status['overall_waitlist']})"
                )

        # Session details
        st.markdown(f"### 📋 Session Information")
        if status["session_date"]:
            st.markdown(f" - **Session Date**: {status['session_date']}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                f"Session {session_number} Participants"
                if session_number
                else "Participants",
                f"{status['total']} / {status['max']}",
            )
            st.metric("Approved Reservations", f"{status['approved']}")

        with col2:
            st.metric("Remaining Spots", f"{status['max'] - status['total']}")

        st.markdown("---")
    else:
        # No active session
        st.success("## ✅ Reservation Open")
        st.info(
            f"📊 {status['total']} / {status['max']} participants (Waitlist: {status['overall_waitlist']})"
        )

    st.markdown("---")

    # Overall statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Current Participants",
            f"{status['overall_total']} / {status['overall_max']}",
        )

    with col2:
        st.metric("Approved Reservations", f"{status['approved']}")

    with col3:
        st.metric("Waitlist", f"{status['overall_waitlist']}")

    st.markdown("---")

    # Login-based messages
    if auth.is_authenticated():
        user = auth.get_current_user()

        st.markdown("### 👤 Welcome!")

        # Blacklist check
        if user and user.get("commander_id"):
            blacklisted = db.check_blacklist(user["commander_id"])

            if blacklisted:
                st.error("⛔ You are registered on the blacklist.")
                st.info("Please contact the administrator.")
                return

        # User info display
        if user:
            st.markdown(f"""
            - **Nickname**: {user.get("nickname", "Unknown")}
            - **Commander ID**: {user.get("commander_id", "N/A")}
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
                st.markdown("### 📊 My Latest Reservation Status")

                # Waitlist info
                if latest_reservation.get("status") == "waitlisted":
                    waitlist_order = latest_reservation.get("waitlist_order")
                    waitlist_position = latest_reservation.get("waitlist_position")
                    st.warning(f"🔵 You are registered on the waiting list.")
                    st.info(f"Waitlist number: {waitlist_order}")
                    st.info(f"Current position: {waitlist_position}")

                    # Estimated waiting time (assuming 1 person leaves per day)
                    if waitlist_position and waitlist_position > 0:
                        expected_days = waitlist_position
                        st.info(f"Estimated waiting time: about {expected_days} days")

                elif latest_reservation.get("status") == "pending":
                    st.success("🟡 Your reservation is pending approval.")
                    st.info("You can participate once approved by administrator.")

                elif latest_reservation.get("status") == "approved":
                    st.success("🟢 Your reservation has been approved!")
                    st.info(
                        f"Approved at: {latest_reservation.get('approved_at', 'N/A')}"
                    )

                elif latest_reservation.get("status") == "rejected":
                    st.error("🔴 Your reservation has been rejected.")
                    if latest_reservation.get("notes"):
                        st.text(f"Notes: {latest_reservation['notes']}")

                elif latest_reservation.get("status") == "cancelled":
                    st.info("⚪ Your reservation has been cancelled.")

                st.markdown(f"Applied at: {latest_reservation['created_at']}")

                # Queue position info
                st.markdown("---")
                st.markdown("### ⏰ Queue Position")

                # My position calculation
                my_order, is_within = get_my_order(user["id"])

                if my_order and is_within:
                    st.success(f"Current position: {my_order} (within capacity)")
                elif my_order:
                    st.warning(f"Current position: {my_order} (outside capacity)")
                else:
                    st.info("No reservation history yet.")

            # New reservation guide
        if not my_reservations:
            st.info("No reservation history yet.")
            st.markdown("---")

            # Show reservation button only if reservation is open
            if user and status["is_session_active"]:
                if status["is_reservation_open"]:
                    if not status["is_full"]:
                        st.markdown("### 📝 Make Reservation")
                        st.info("Click the button below to make your reservation!")
                    else:
                        st.warning(
                            "⚠️ Current session is full. Reservations will be added to waiting list."
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
                    st.error("⛔ Reservation is closed for this session.")
                else:
                    # Reservation not yet open
                    st.warning("⏰ Reservations are not open yet.")
                    if status["reservation_open_time"]:
                        st.info(
                            f"📅 Reservations open at: {status['reservation_open_time']}"
                        )
            elif user and not status["is_session_active"]:
                st.markdown("### 📝 Make Reservation")

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
        st.markdown("### 📋 Main Information")

        st.markdown("""
        - **First-come, first-served reservation**: Those who reserve first get priority
        - **Maximum participants**: 180 per session
        - **Waiting list system**: Automatically adds to waiting list when capacity exceeded
        - **Commander ID**: Can register with 10-digit number
        - **Password**: Minimum 8 characters

        ## Session-based System

        - When session is full, automatically switches to waiting list registration
        - Previous participants get priority in existing sessions
        - New participants can reserve in new sessions
        - When session is full, shows 'Session Full - Waiting List Only' message

        ## Priority System

        **1st Priority**: Previous participants (from previous sessions)
        - Within capacity: Can reserve in order of registration

        **2nd Priority**: Session-based first-come reservation
        - Can participate in reservation order

        ## When Session is Full

        - When reservation is full, shows '[N] Session Full - Waiting List Only' message
        - Waiting list numbers are assigned in reservation order.
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
                        f"Author: {ann.get('author_name', 'Unknown')} | Created: {ann['created_at'][:19]}"
                    )
        else:
            st.info("No registered announcements.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>©2026 DaWn Dice Party by Entity</div>",
        unsafe_allow_html=True,
    )

    # Admin-only messages
    if auth.is_admin():
        st.markdown("---")
        st.info("Admin Menu")

        # Admin dashboard link
        st.markdown("[📊 Go to Dashboard to check current status")

        # Admin announcements link
        st.markdown("[📢 Go to Announcements to create session announcements")

        # Admin event sessions link
        st.markdown("[🎲 Go to Event Sessions to manage session reservations")
