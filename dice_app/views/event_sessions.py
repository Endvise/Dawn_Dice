#!/usr/bin/env python3
"""
Event Sessions Management Page
"""

import streamlit as st
import database as db
import auth
from datetime import datetime, date, timedelta
from typing import Optional


def show():
    """Show event sessions management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Event Sessions Management")
    st.markdown("---")

    current_session = get_active_session()

    if current_session:
        st.info(
            f"Current active session: **{current_session['session_number']}** ({current_session['session_name']})"
        )
        st.warning(
            "A session is currently active. Deactivate it first to create a new session."
        )
    else:
        st.success("No active session. You can create a new session.")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Sessions List", "Create Session", "Settings"])

    with tab1:
        st.markdown("### Sessions List")

        sessions = get_all_sessions()

        if sessions:
            for session in sessions:
                if session["is_active"]:
                    status_badge = "✅ Active"
                    status_color = "success"
                else:
                    status_badge = "⏳ Inactive"
                    status_color = "info"

                participant_count = get_participant_count(session["id"])
                approved_count = get_approved_reservation_count(session["id"])

                with st.expander(
                    f"{status_badge} Session {session['session_number']} - {session['session_name']}"
                ):
                    st.markdown(f"""
                    **Session Name**: {session["session_name"]}
                    **Session Date**: {session["session_date"]}
                    **Max Participants**: {session["max_participants"]}
                    **Participants**: {participant_count} (existing) + {approved_count} (reservations) = {participant_count + approved_count}
                    **Created By**: {session.get("creator_name", "Unknown")}
                    **Created At**: {session["created_at"]}
                    """)

                    if (
                        participant_count + approved_count
                        >= session["max_participants"]
                    ):
                        st.error(
                            "Session is full! New reservations will be added to waitlist."
                        )
                    else:
                        remaining = session["max_participants"] - (
                            participant_count + approved_count
                        )
                        st.success(f"Remaining spots: {remaining}")

                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown("### Actions")

                        if session["is_active"]:
                            if st.button(
                                "Deactivate",
                                key=f"deactivate_{session['id']}",
                                use_container_width=True,
                            ):
                                if st.button(
                                    f"Deactivate Session {session['session_number']}?",
                                    key=f"confirm_deactivate_{session['id']}",
                                ):
                                    update_session_active(session["id"], False)
                                    st.success("Session deactivated.")
                                    st.rerun()
                        else:
                            if st.button(
                                "Activate",
                                key=f"activate_{session['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                other_active = get_active_session()
                                if other_active and other_active["id"] != session["id"]:
                                    st.error(
                                        f"Session {other_active['session_number']} is already active. Deactivate it first."
                                    )
                                else:
                                    update_session_active(session["id"], True)
                                    st.success(
                                        f"Session {session['session_number']} activated."
                                    )
                                    st.rerun()

                            if is_master:
                                if st.button(
                                    "Delete",
                                    key=f"delete_{session['id']}",
                                    type="secondary",
                                    use_container_width=True,
                                ):
                                    if st.button(
                                        f"Delete Session {session['session_number']}? This cannot be undone.",
                                        key=f"confirm_delete_{session['id']}",
                                    ):
                                        delete_session(session["id"])
                                        st.success("Session deleted.")
                                        st.rerun()

                    with col2:
                        st.markdown("### Reservations")

                        session_reservations = get_session_reservations(session["id"])

                        st.metric("Total", f"{len(session_reservations)}")

                        pending = len(
                            [
                                r
                                for r in session_reservations
                                if r["status"] == "pending"
                            ]
                        )
                        approved = len(
                            [
                                r
                                for r in session_reservations
                                if r["status"] == "approved"
                            ]
                        )
                        waitlisted = len(
                            [
                                r
                                for r in session_reservations
                                if r["status"] == "waitlisted"
                            ]
                        )

                        st.markdown(f"""
                        - Pending: {pending}
                        - Approved: {approved}
                        - Waitlist: {waitlisted}
                        """)

                    with col3:
                        st.markdown("### Participants")

                        participants = get_session_participants(session["id"])

                        if participants:
                            for p in participants[:5]:
                                st.text(f"- {p['nickname']} ({p.get('igg_id', 'N/A')})")

                            if len(participants) > 5:
                                st.text(f"... and {len(participants) - 5} more")
                        else:
                            st.info("No participants.")
        else:
            st.info("No registered sessions.")

    with tab2:
        st.markdown("### Create Session")

        if current_session:
            st.error("Cannot create a new session while a session is active.")
            return

        col1, col2 = st.columns([1, 2])

        with col1:
            session_number = st.number_input(
                "Session Number",
                min_value=1,
                step=1,
                value=get_next_session_number(),
                key="session_number",
            )

            session_name = st.text_input(
                "Session Name", placeholder="e.g., 260128 Dice Party"
            )

            today = date.today()
            min_date = today + timedelta(days=1)
            session_date = st.date_input(
                "Session Date", min_value=min_date, value=min_date
            )

            max_participants = st.number_input(
                "Max Participants", min_value=1, value=180, step=10
            )

        with col2:
            st.markdown("### Reservation Time Settings")

            st.info("""
            **Reservation Open Time:**
            - Set when reservations open for this session
            - If not set, reservations are open immediately when session is created
            - Users can see countdown timer on homepage

            **Reservation Close Time:**
            - Set when reservations close for this session
            - After this time, no new reservations can be made
            - If not set, reservations stay open until session is full
            """)

            # Reservation time settings
            col_time1, col_time2 = st.columns(2)

            with col_time1:
                enable_open_time = st.checkbox(
                    "Set Reservation Open Time", key="enable_open_time"
                )
                if enable_open_time:
                    reservation_open_time = st.datetime_input(
                        "Reservation Open Time",
                        value=datetime.now() + timedelta(hours=1),
                        key="reservation_open_time",
                    )
                else:
                    reservation_open_time = None

            with col_time2:
                enable_close_time = st.checkbox(
                    "Set Reservation Close Time", key="enable_close_time"
                )
                if enable_close_time:
                    reservation_close_time = st.datetime_input(
                        "Reservation Close Time",
                        value=datetime.now() + timedelta(days=1),
                        key="reservation_close_time",
                    )
                else:
                    reservation_close_time = None

        st.markdown("---")

        # Guide
        st.markdown("### Guide")

        col_guide1, col_guide2 = st.columns([1, 2])

        with col_guide1:
            st.markdown("""
            - **Session Number**: Auto-increment (next available)
            - **Session Name**: e.g., "260128 Dice Party"
            - **Session Date**: Scheduled event date
            - **Max Participants**: Default 180

            **Session Activation:**
            - Automatically activated upon creation
            - Previous sessions are auto-deactivated
            - Only active sessions accept reservations

            **Priority:**
            - 1st Priority: Existing participants (previous sessions)
            - 2nd Priority: External participants (new signups)
            """)

        with col_guide2:
            st.markdown("""
            **Reservation Time Settings:**

            - **Countdown Timer**: Users see countdown on homepage until reservations open
            - **First-Come-First-Served**: Once open, users compete for spots
            - **Capacity Limit**: Auto switch to waitlist when full
            - **Close Time**: After close time, no more reservations accepted

            **Example Timeline:**
            1. Create session with open time: 8:00 PM
            2. Users see countdown on homepage
            3. At 8:00 PM, reservations open
            4. First users to submit get spots
            5. At close time, reservation closes
            """)

        st.markdown("---")
        if st.button("Create Session", type="primary", use_container_width=True):
            if not session_name:
                st.error("Enter session name.")
                return

            # user_id가 None인지 확인
            user_id = user.get("id") if user else None
            if not user_id:
                st.error("User ID not found. Please log in again.")
                return

            if enable_open_time and enable_close_time:
                if reservation_open_time and reservation_close_time:
                    if reservation_open_time >= reservation_close_time:
                        st.error("Open time must be before close time.")
                        return

            try:
                create_session(
                    session_number=session_number,
                    session_name=session_name,
                    session_date=session_date,
                    max_participants=max_participants,
                    created_by=user_id,
                    reservation_open_time=reservation_open_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if reservation_open_time
                    else None,
                    reservation_close_time=reservation_close_time.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if reservation_close_time
                    else None,
                )

                st.success(f"Session {session_number} created.")
                if reservation_open_time:
                    st.info(
                        f"Reservations will open at: {reservation_open_time.strftime('%Y-%m-%d %H:%M')}"
                    )
                else:
                    st.info("Reservations are now open!")
                st.rerun()

            except Exception as e:
                st.error(f"Error creating: {e}")

    with tab3:
        st.markdown("### Session Settings")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Existing Participant Priority")

            st.info("""
            **Priority Settings:**

            **1st Priority: Existing Participants**
            - Previous session participants get priority for new session reservations
            - Users with participation records get priority booking
            - Users without records wait

            **2nd Priority: External Participants**
            - New signups have no participation records
            - Can reserve remaining spots after existing participants
            """)

        with col2:
            st.markdown("### Waitlist System")

            st.info(f"""
            **Waitlist System:**

            - Session capacity: {db.MAX_PARTICIPANTS}
            - When full: Auto register to waitlist
            - Waitlist number: First-come, first-served
            - Approval: Can approve in waitlist order

            **Key:**
            - Spots filled by existing participants first
            - Remaining spots go to external participants
            """)

        st.markdown("---")
        st.markdown("### Announcement Guide")

        st.info("""
        **Create Announcement When Session is Full:**

        1. Check when session reaches capacity
        2. Write announcement in "Announcements Management"
        3. Displayed on homepage for users
        4. Example: "[Session 2] Reservations Closed - Confirmed Jan 31"

        **Announcement Example:**
        ```markdown
        # [Session 2] Reservation Closed

        Hello! Session 2 reservations are closed.

        ## Schedule
        - **Confirmation**: Jan 31, 8 PM
        - **Location**: Online Discord

        ## Important
        - Capacity: 180
        - Deadline: Tomorrow 8 PM
        - First-come, first-served

        ## Priority
        1. Session 1 participants
        2. New signups
        ```

        **Before Session Starts:**
        - Session start announcement
        - Participation instructions
        - Important notices
        """)


# Helper Functions


def get_all_sessions():
    """Return all sessions."""
    return db.get_all_sessions()


def get_active_session():
    """Return active session."""
    return db.get_active_session()


def get_next_session_number():
    """Return next session number."""
    return db.get_next_session_number()


def get_participant_count(session_id: str) -> int:
    """Return participant count for session."""
    return db.get_participant_count(session_id)


def get_approved_reservation_count(session_id: str) -> int:
    """Return approved reservation count for session."""
    return db.get_approved_reservation_count(session_id)


def get_session_reservations(session_id: str):
    """Return reservations for session."""
    return db.get_session_reservations(session_id)


def get_session_participants(session_id: str):
    """Return participants for session."""
    return db.get_session_participants(session_id)


def update_session_active(session_id: str, is_active: bool):
    """Update session active status."""
    db.update_session_active(session_id, is_active)


def delete_session(session_id: str):
    """Delete session."""
    db.delete_session(session_id)


def create_session(
    session_number: int,
    session_name: str,
    session_date: date,
    max_participants: int,
    created_by: str,
    reservation_open_time: Optional[str] = None,
    reservation_close_time: Optional[str] = None,
):
    """Create new session."""
    db.create_session(
        session_number=session_number,
        session_name=session_name,
        session_date=session_date,
        max_participants=max_participants,
        created_by=created_by,
        reservation_open_time=reservation_open_time,
        reservation_close_time=reservation_close_time,
    )
