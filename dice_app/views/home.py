#!/usr/bin/env python3
"""
메인 홈페이지 - 회차별 예약 시스템 포함
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def get_reservation_status() -> Dict[str, Any]:
    """예약 상태를 반환합니다."""
    # 기존 참여자 수
    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    )
    participants_count = result["count"] if result else 0

    # 승인된 예약자 수
    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    approved_count = result["count"] if result else 0

    # 전체 참여자 수
    total_count = participants_count + approved_count

    # 현재 활성화된 회차 확인
    active_session = get_active_session()

    if active_session:
        # 회차별 참여자 수
        session_id = active_session["id"]
        session_name = active_session.get("session_name", "")
        max_participants = active_session.get("max_participants", db.MAX_PARTICIPANTS)

        # 회차별 승인된 예약 수
        result = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE event_name = ? AND status = 'approved'",
            (session_name,),
            fetch="one",
        )
        session_approved_count = result["count"] if result else 0

        # 총 참여자 수 (기존 + 회차별 승인)
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

        return {
            "total": session_count,
            "max": max_participants,
            "approved": session_approved_count,
            "is_full": session_count >= max_participants,
            "session_number": active_session["session_number"],
            "session_name": session_name,
            "session_date": active_session.get("session_date"),
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
            "is_session_active": False,
            "overall_total": total_count,
            "overall_max": db.MAX_PARTICIPANTS,
            "overall_is_full": total_count >= db.MAX_PARTICIPANTS,
            "overall_waitlist": waitlist_count,
        }


def get_active_session() -> Optional[Dict[str, Any]]:
    """활성화된 회차를 반환합니다."""
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
    """내 순위를 반환합니다. (순위, 정원 여부)"""
    # 기존 참여자 수
    participants_count = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    ).get("count", 0)

    # 승인된 예약자 수
    approved_count = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    ).get("count", 0)

    # 내 예약
    my_reservations = execute_query(
        "SELECT * FROM reservations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
        fetch="one",
    )

    if not my_reservations:
        return None, False

    # 선착순위 계산
    total_before_me = participants_count + approved_count

    if my_reservations["status"] == "approved":
        my_order = total_before_me
    elif my_reservations["status"] in ["pending", "waitlisted"]:
        my_order = total_before_me + 1
    else:
        my_order = total_before_me

    return my_order, my_order <= db.MAX_PARTICIPANTS


def show():
    """메인 페이지 표시"""
    st.set_page_config(
        page_title="DaWn Dice Party",
        page_icon="🎲",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 앱 초기화
    db.init_app()

    # 세션 초기화
    auth.init_session_state()

    # 개발자 도구 방지 (관리자 제외)
    import security_utils

    security_utils.inject_devtools_block()

    # Home page
    st.title("🎲 DaWn Dice Party")
    st.markdown("by Entity")
    st.markdown("---")

    # Reservation status display
    status = get_reservation_status()

    # 활성화된 회차가 있으면 회차별 정보 표시
    if status["is_session_active"]:
        st.error(
            f"## ⛔ {status['session_number']}회차 예약 마감 [대기순번 등록만 가능]"
        )
        st.info(
            f"현재 {status['total']}명 / {status['max']}명 (대기자: {status['overall_waitlist']}명)"
        )

        # 회차별 상세 정보
        st.markdown(f"### 📋 {status['session_name']}회차 정보")
        st.markdown(f" - **회차 번호**: {status['session_number']}")
        st.markdown(f" - **회차 날짜**: {status['session_date']}")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                f"{status['session_number']}회차 참여자",
                f"{status['total']} / {status['max']}명",
            )
            st.metric("승인된 예약", f"{status['approved']}건")

        with col2:
            st.metric("남은 자리", f"{status['max'] - status['total']}명")

        st.markdown("---")
    else:
        st.success(f"## ✅ 예약 가능")
        st.info(
            f"현재 {status['total']}명 / {status['max']}명 (대기자: {status['overall_waitlist']}명)"
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "현재 참여자", f"{status['overall_total']} / {status['overall_max']}명"
        )

    with col2:
        st.metric("승인된 예약", f"{status['approved']}명")

    with col3:
        st.metric("대기자", f"{status['overall_waitlist']}명")

    st.markdown("---")

    # Login-based messages
    if auth.is_authenticated():
        user = auth.get_current_user()

        st.markdown("### 👤 Welcome!")

        # Blacklist check
        if user.get("commander_id"):
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
                    if waitlist_position > 0:
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

            if user and not status["is_session_active"]:
                st.markdown("### 📝 Make Reservation")
            elif user:
                st.warning(
                    "⚠️ Current session is full. Reservations will be added to waiting list."
                )

            if user and st.button(
                "Go to Reservation", use_container_width=True, type="primary"
            ):
                st.session_state["page"] = "reservation"
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

            # Registration button (outside form)
            if st.button("Sign Up", use_container_width=True):
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
                    "공지": "📢",
                    "안내": "ℹ️",
                    "이벤트": "🎉",
                    "notice": "📢",
                    "guide": "ℹ️",
                    "event": "🎉",
                }

                badge = category_badge.get(ann.get("category", "공지"), "📢")

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

    # 사용자별 메시지 (관리자 전용)
    if auth.is_admin():
        st.markdown("---")
        st.info("💡 관리자 전용 메시지")

        # 관리자 전용 대시보드 바로가기 링크
        st.markdown("[📊 대시보드로 이동하면 현재 상태를 확인할 수 있습니다.")

        # 관리자 전용 공지사항 바로가기 링크
        st.markdown("[📢 공지사항 관리로 이동하면 회차별 공지를 작성할 수 있습니다.")

        # 관리자 전용 회차 관리 바로가기 링크
        st.markdown("[🎲 회차 관리로 이동하면 회차별 예약을 관리할 수 있습니다.")
