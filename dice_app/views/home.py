#!/usr/bin/env python3
"""
Main Homepage - Session-based Reservation System
"""

import streamlit as st
import database as db
import auth
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def get_reservation_status() -> Dict[str, Any]:
    """Returns reservation status."""
    # Get participants and reservations
    participants = db.list_participants()
    reservations = db.list_reservations()

    # Existing participants count (completed)
    participants_count = len([p for p in participants if p.get("completed")])

    # Approved reservations count
    approved_count = len(reservations)

    # Total participants
    total_count = participants_count + approved_count

    # Get current active session
    active_session = db.get_active_session()

    if active_session:
        session_id = active_session.get("id")
        session_name = active_session.get("session_name", "")
        session_number = active_session.get("session_number", "")
        max_participants = active_session.get("max_participants", db.MAX_PARTICIPANTS)
        reservation_open_time = active_session.get("reservation_open_time")
        reservation_close_time = active_session.get("reservation_close_time")
        session_date = active_session.get("session_date")

        # Calculate session counts
        session_participants = len([p for p in participants if p.get("completed")])
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
            "is_reservation_open": True,  # No session = always open
            "is_reservation_closed": False,
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


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
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
            st.markdown(f"## 🎯 제 {session_number}회차 예약")
        if session_name:
            st.markdown(f"### 📅 {session_name}")

        # Reservation status display
        if status["is_reservation_closed"]:
            st.error("## ⛔ 예약 마감")
        elif status["is_reservation_open"]:
            if status["is_full"]:
                st.warning("## ⏳ 대기 등록만 가능")
            else:
                st.success("## ✅ 예약 접수 중")
        else:
            st.info("## ⏰ 예약 오픈 예정")

        # Time information
        col_time1, col_time2 = st.columns(2)

        with col_time1:
            if status["reservation_open_time"]:
                st.info(
                    f"📅 **예약 오픈 시간**: {format_datetime(status['reservation_open_time'])}"
                )
            else:
                st.info("📅 **예약 오픈 시간**: 즉시")

        with col_time2:
            if status["reservation_close_time"]:
                st.info(
                    f"⏰ **예약 마감 시간**: {format_datetime(status['reservation_close_time'])}"
                )
            else:
                st.info("⏰ **예약 마감 시간**: 정원 소진 시")

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
                st.markdown("### ⏱️ 예약 오픈까지 남은 시간")
                col_cd1, col_cd2, col_cd3, col_cd4 = st.columns(4)
                with col_cd1:
                    st.metric("일", time_remaining["days"])
                with col_cd2:
                    st.metric("시", time_remaining["hours"])
                with col_cd3:
                    st.metric("분", time_remaining["minutes"])
                with col_cd4:
                    st.metric("초", time_remaining["seconds"])

        st.markdown("---")

        # Capacity and waitlist info
        st.markdown("### 📊 정원 현황")

        if status["is_full"]:
            # 정원 초과 - 대기 등록만 가능
            remaining = status["remaining_spots"]
            st.error(
                f"⚠️ **정원이 초과되었습니다!**\n\n"
                f"현재 {status['total']} / {status['max']}명 참여 중\n"
                f"대기 등록 가능 자리: {remaining}자리\n\n"
                f"💬 **대기 등록 시 관리자가 인게임에서 별도로 DM을 보낼 예정입니다.**"
            )
        else:
            # 정원 남아있음
            remaining = status["max"] - status["total"]
            st.success(
                f"🎉 **예약 접수 중!**\n\n"
                f"현재 {status['total']} / {status['max']}명 참여 중\n"
                f"남은 자리: {remaining}자리"
            )

        # Progress bar
        progress = min(status["total"] / status["max"], 1.0)
        st.progress(progress)

        # Session details
        if session_date:
            st.markdown(f"### 📋 세션 정보")
            st.markdown(f"- **일시**: {session_date}")

        st.markdown("---")
    else:
        # No active session
        st.success("## ✅ 예약 접수 중")
        st.info(f"📊 {status['total']} / {status['max']}명 참여 중")

    st.markdown("---")

    # Overall statistics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "현재 참여자",
            f"{status['overall_total']} / {status['overall_max']}",
        )

    with col2:
        st.metric("예약 확정", f"{status['approved']}")

    with col3:
        st.metric("남은 자리", f"{status['overall_max'] - status['overall_total']}")

    st.markdown("---")

    st.markdown("---")

    # Login-based messages
    if auth.is_authenticated():
        user = auth.get_current_user()

        st.markdown("### 👤 안녕하세요!")

        # Blacklist check
        if user:
            commander_number = user.get("commander_number") or user.get("username")
            if commander_number:
                blacklisted = db.check_blacklist(commander_number)

                if blacklisted:
                    st.error("⛔ 블랙리스트에 등록되어 있습니다.")
                    st.info("관리자에게 문의하세요.")
                    return

        # User info display
        if user:
            st.markdown(f"""
            - **닉네임**: {user.get("nickname", "Unknown")}
            - **사령관번호**: {user.get("commander_number", "N/A")}
            - **서버**: {user.get("server", "N/A")}
            - **연맹**: {user.get("alliance", "없음") if user.get("alliance") else "없음"}
            """)

        # My reservations status
        my_reservations = []
        if user:
            my_reservations = db.list_reservations(user_id=user["id"])

            if my_reservations:
                latest_reservation = my_reservations[0]

                st.markdown("---")
                st.markdown("### 📊 내 예약 현황")

                st.success(f"🎉 예약이 완료되었습니다!")

                st.markdown(
                    f"**예약일시**: {latest_reservation.get('created_at', 'N/A')}"
                )

                # Queue position info
                st.markdown("---")
                st.markdown("### ⏰ 예약 순서")

                total = status["total"]
                max_capacity = status["max"]

                if total < max_capacity:
                    st.success(f"현재 {total}번째 예약자입니다. (정원 내)")
                else:
                    position = total - max_capacity + 1
                    st.warning(f"현재 {total}번째 예약자입니다. (대기 {position}번째)")

            # New reservation guide
        if not my_reservations:
            st.info("아직 예약이 없습니다.")
            st.markdown("---")

            # Show reservation button only if reservation is open
            if user and status["is_session_active"]:
                if status["is_reservation_open"]:
                    if not status["is_full"]:
                        st.markdown("### 📝 예약 신청")
                        st.info("아래 버튼을 클릭하여 예약을 진행하세요!")
                    else:
                        st.warning(
                            "⚠️ 현재 정원이 초과되었습니다. 대기 등록만 가능합니다."
                        )
                    if st.button(
                        "예약 신청하기",
                        use_container_width=True,
                        type="primary",
                        key=f"home_go_to_reservation_{user['id']}"
                        if user
                        else "home_go_to_reservation",
                    ):
                        st.session_state["page"] = "📝 Make Reservation"
                        st.rerun()
                elif status["is_reservation_closed"]:
                    st.error("⛔ 예약이 마감되었습니다.")
                else:
                    # Reservation not yet open
                    st.warning("⏰ 예약이 아직 열리지 않았습니다.")
                    if status["reservation_open_time"]:
                        st.info(
                            f"📅 예약 오픈 시간: {format_datetime(status['reservation_open_time'])}"
                        )
            elif user and not status["is_session_active"]:
                st.markdown("### 📝 예약 신청")

                if st.button(
                    "예약 신청하기",
                    use_container_width=True,
                    type="primary",
                    key=f"home_go_to_reservation_{user['id']}"
                    if user
                    else "home_go_to_reservation",
                ):
                    st.session_state["page"] = "📝 Make Reservation"
                    st.rerun()

    else:
        st.markdown("### 👋 환영합니다!")
        st.markdown("DaWn Dice Party에 오신 것을 환영합니다!")
        st.markdown("---")

        # Login button area (left aligned)
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown("### 📝 로그인")

            # Login form
            with st.form("login_form"):
                username = st.text_input(
                    "사령관번호 또는 아이디", key="home_login_username"
                )
                password = st.text_input(
                    "비밀번호", type="password", key="home_login_password"
                )

                submitted = st.form_submit_button(
                    "로그인", use_container_width=True, type="primary"
                )

                if submitted:
                    success, message = auth.login(username, password)

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            # Sign Up button (outside form)
            if st.button("회원가입", use_container_width=True, key="home_register"):
                st.session_state["show_register"] = True
                st.rerun()

        st.markdown("---")

        # Main information
        st.markdown("### 📋 안내사항")

        st.markdown("""
        - **선착순 예약**: 먼저 예약하는 사람이 우선순위
        - **최대 참여자**: 세션당 180명
        - **대기자 시스템**: 정원 초과 시 자동 대기로 등록
        - **사령관번호**: 10자리 숫자로 가입
        - **비밀번호**: 최소 8자 이상

        ## 세션 기반 시스템

        - 세션이 가득 차면 자동으로 대기자 등록으로 전환
        - 기존 참여자는 우선순위
        - 새로운 참여자는 새로운 세션에서 예약 가능
        - 정원 초과 시 '정원 초과 - 대기자 등록만 가능' 메시지 표시

        ## 우선순위 시스템

        **1순위**: 기존 참여자 (이전 세션 참여자)
        - 정원 내에서는 예약 순서대로 참여 가능

        **2순위**: 세션별 선착순 예약
        - 예약 순서대로 참여 가능

        ## 정원 초과 시

        - 정원 초과 시 '제N회차 정원 초과 - 대기자 등록만 가능' 메시지 표시
        - 대기자 번호는 예약 순서대로 배정됩니다.
        """)

        st.markdown("---")

        # Announcements display
        st.markdown("### 📢 공지사항")

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
                pin_indicator = " 📌 고정" if ann.get("is_pinned") else ""

                with st.expander(f"{badge} {ann['title']}{pin_indicator}"):
                    st.markdown(ann["content"])

                    st.markdown(
                        f"작성자: {ann.get('author_name', 'Unknown')} | 작성일: {ann.get('created_at', 'N/A')}"
                    )
        else:
            st.info("등록된 공지사항이 없습니다.")

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
                        f"작성자: {ann.get('author_name', 'Unknown')} | 작성일: {ann.get('created_at', 'N/A')}"
                    )
        else:
            st.info("등록된 공지사항이 없습니다.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>©2026 DaWn Dice Party by Entity</div>",
        unsafe_allow_html=True,
    )

    # Admin-only messages
    if auth.is_admin():
        st.markdown("---")
        st.info("관리자 메뉴")

        # Admin dashboard link
        st.markdown("[📊 대시보드로 이동 - 현재 상태 확인")

        # Admin announcements link
        st.markdown("[📢 공지사항 관리로 이동 - 세션 공지 작성")

        # Admin event sessions link
        st.markdown("[🎲 세션 관리로 이동 - 예약 관리")
