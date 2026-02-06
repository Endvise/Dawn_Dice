#!/usr/bin/env python3
"""
Session Check-in Management Page
세션별 참여자 체크인 관리 시스템
"""

import streamlit as st
import auth
import database as db


def show():
    """Main function - Render page"""
    st.title("🎯 Session Check-in Management")

    # Get active session
    active_session = db.get_active_session()
    if not active_session:
        st.warning("No active session. Please create a session first.")
        return

    session_id = str(active_session["id"])
    session_name = active_session.get(
        "session_name", f"Session {active_session.get('session_number', '?')}"
    )

    st.markdown(f"**Current Session:** {session_name}")

    # Get current user info for checked_by
    current_user = auth.get_current_user()
    checked_by = current_user.get("username", "admin") if current_user else "admin"

    # Tab selection
    tab1, tab2, tab3 = st.tabs(
        ["📋 Participant List", "🔍 Quick Check", "📊 Statistics"]
    )

    with tab1:
        render_participant_list_tab(session_id, checked_by)

    with tab2:
        render_quick_check_tab(session_id, checked_by)

    with tab3:
        render_statistics_tab(session_id)


def render_participant_list_tab(session_id: str, checked_by: str):
    """Tab 1: Participant List with checkbox management"""
    st.subheader("📋 Participant List")

    # Get participants
    participants = db.get_session_participants_check(session_id)

    if not participants:
        st.info("No participants in this session yet.")
        return

    # Filter options
    filter_type = st.selectbox(
        "Filter by Status",
        [
            "All",
            "Pending",
            "Re-confirmed",
            "Alliance Entry",
            "Dice Purchased",
            "Completed All",
        ],
    )

    # Filter participants
    filtered_participants = participants
    if filter_type == "Pending":
        filtered_participants = [
            p
            for p in participants
            if not (
                p.get("re_confirmed")
                and p.get("alliance_entry")
                and p.get("dice_purchased")
            )
        ]
    elif filter_type == "Re-confirmed":
        filtered_participants = [p for p in participants if p.get("re_confirmed")]
    elif filter_type == "Alliance Entry":
        filtered_participants = [p for p in participants if p.get("alliance_entry")]
    elif filter_type == "Dice Purchased":
        filtered_participants = [p for p in participants if p.get("dice_purchased")]
    elif filter_type == "Completed All":
        filtered_participants = [
            p
            for p in participants
            if p.get("re_confirmed")
            and p.get("alliance_entry")
            and p.get("dice_purchased")
        ]

    st.markdown(f"**Total Participants:** {len(filtered_participants)}")

    # Display participants
    for p in filtered_participants:
        with st.expander(
            f"👤 {p.get('nickname', 'Unknown')} ({p.get('commander_id', 'N/A')}) - {p.get('server', '')}"
        ):
            col1, col2, col3 = st.columns(3)

            # Re-confirmed toggle
            with col1:
                re_confirmed = p.get("re_confirmed", False)
                if st.button(
                    "✅ Re-confirmed" if re_confirmed else "⭕ Re-confirm",
                    key=f"reconfirmed_{p['id']}",
                    help="Toggle re-confirmation status",
                ):
                    db.toggle_session_check(
                        session_id, p["commander_id"], "re_confirmed", checked_by
                    )
                    st.rerun()

            # Alliance entry toggle
            with col2:
                alliance_entry = p.get("alliance_entry", False)
                if st.button(
                    "✅ Alliance Entry" if alliance_entry else "⭕ Alliance Entry",
                    key=f"alliance_{p['id']}",
                    help="Toggle alliance entry status",
                ):
                    db.toggle_session_check(
                        session_id, p["commander_id"], "alliance_entry", checked_by
                    )
                    st.rerun()

            # Dice purchased toggle
            with col3:
                dice_purchased = p.get("dice_purchased", False)
                if st.button(
                    "✅ Dice Purchased" if dice_purchased else "⭕ Dice Purchased",
                    key=f"dice_{p['id']}",
                    help="Toggle dice purchase status",
                ):
                    db.toggle_session_check(
                        session_id, p["commander_id"], "dice_purchased", checked_by
                    )
                    st.rerun()

            # Info
            st.markdown("---")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.markdown(f"**Alliance:** {p.get('alliance', '-')}")
            with info_col2:
                st.markdown(f"**Checked by:** {p.get('checked_by', '-') or '-'}")

            checked_at = p.get("checked_at")
            if checked_at:
                st.markdown(f"**Last checked:** {checked_at}")

            notes = p.get("notes")
            if notes:
                st.markdown(f"**Notes:** {notes}")


def render_quick_check_tab(session_id: str, checked_by: str):
    """Tab 2: Quick Check by Commander ID"""
    st.subheader("🔍 Quick Check")

    st.info("Enter Commander ID to quickly check/uncheck status")

    # Check type selection
    check_type = st.radio(
        "Select Check Type",
        ["re_confirmed", "alliance_entry", "dice_purchased"],
        format_func=lambda x: {
            "re_confirmed": "🔄 Re-confirmed",
            "alliance_entry": "🤝 Alliance Entry",
            "dice_purchased": "🎲 Dice Purchased",
        }[x],
    )

    # Commander ID input
    commander_id = st.text_input(
        "Commander ID", placeholder="Enter 10-digit Commander ID"
    )

    if commander_id:
        # Find participant
        participant = db.get_participant_by_commander(session_id, commander_id)

        if participant:
            st.success(f"Found: {participant.get('nickname', 'Unknown')}")

            # Show current status
            current_status = participant.get(check_type, False)
            st.markdown(
                f"**Current Status:** {'✅ Checked' if current_status else '❌ Not Checked'}"
            )

            # Toggle button
            action = "Uncheck" if current_status else "Check"
            if st.button(
                f"{'✅' if current_status else '⭕'} {action}", type="primary"
            ):
                success, new_state = db.toggle_session_check(
                    session_id, commander_id, check_type, checked_by
                )
                if success:
                    st.success(
                        f"Status changed to: {'Checked' if new_state else 'Unchecked'}"
                    )
                else:
                    st.error("Failed to update status")
                st.rerun()
        else:
            st.warning("Participant not found in this session.")
            st.markdown("Would you like to add this participant?")

            # Quick add form
            with st.form("quick_add_form"):
                nickname = st.text_input("Nickname")
                server = st.text_input("Server", placeholder="#000")
                alliance = st.text_input("Alliance")

                if st.form_submit_button("➕ Add Participant"):
                    result = db.add_participant_to_session(
                        session_id=session_id,
                        commander_id=commander_id,
                        nickname=nickname,
                        server=server,
                        alliance=alliance,
                    )
                    if result > 0:
                        st.success("Participant added!")
                        st.rerun()
                    else:
                        st.error("Failed to add participant")


def render_statistics_tab(session_id: str):
    """Tab 3: Check-in Statistics"""
    st.subheader("📊 Session Check-in Statistics")

    # Get statistics
    stats = db.get_session_check_stats(session_id)

    if stats["total"] == 0:
        st.info("No participants in this session.")
        return

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Participants", stats["total"], delta=None)

    with col2:
        st.metric(
            "Re-confirmed",
            f"{stats['re_confirmed']} ({stats['re_confirmed_percent']}%)",
            delta=f"+{stats['re_confirmed']}" if stats["re_confirmed"] > 0 else None,
        )

    with col3:
        st.metric(
            "Alliance Entry",
            f"{stats['alliance_entry']} ({stats['alliance_entry_percent']}%)",
            delta=f"+{stats['alliance_entry']}"
            if stats["alliance_entry"] > 0
            else None,
        )

    with col4:
        st.metric(
            "Dice Purchased",
            f"{stats['dice_purchased']} ({stats['dice_purchased_percent']}%)",
            delta=f"+{stats['dice_purchased']}"
            if stats["dice_purchased"] > 0
            else None,
        )

    st.markdown("---")

    # Progress bars
    st.markdown("### Progress")

    # Re-confirmed progress
    st.markdown("**Re-confirmed Progress**")
    st.progress(stats["re_confirmed_percent"] / 100)
    st.markdown(
        f"{stats['re_confirmed']} / {stats['total']} ({stats['re_confirmed_percent']}%)"
    )

    # Alliance entry progress
    st.markdown("**Alliance Entry Progress**")
    st.progress(stats["alliance_entry_percent"] / 100)
    st.markdown(
        f"{stats['alliance_entry']} / {stats['total']} ({stats['alliance_entry_percent']}%)"
    )

    # Dice purchased progress
    st.markdown("**Dice Purchased Progress**")
    st.progress(stats["dice_purchased_percent"] / 100)
    st.markdown(
        f"{stats['dice_purchased']} / {stats['total']} ({stats['dice_purchased_percent']}%)"
    )

    # Completion rate
    completed_all = sum(
        1
        for p in db.get_session_participants_check(session_id)
        if p.get("re_confirmed") and p.get("alliance_entry") and p.get("dice_purchased")
    )
    completion_rate = (
        round((completed_all / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
    )

    st.markdown("---")
    st.markdown(f"### 🎉 Complete (All 3): {completed_all} ({completion_rate}%)")
    st.progress(completion_rate / 100)


if __name__ == "__main__":
    show()
