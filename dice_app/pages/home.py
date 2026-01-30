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

    # 홈페이지
    st.title("🎲 DaWn Dice Party")
    st.markdown("by 엔티티")
    st.markdown("---")

    # 예약 상태 표시
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

    # 로그인 여부에 따른 메시지
    if auth.is_authenticated():
        user = auth.get_current_user()

        st.markdown("### 👤 환영합니다!")

        # 블랙리스트 체크
        if user.get("commander_id"):
            blacklisted = db.check_blacklist(user["commander_id"])

            if blacklisted:
                st.error("⛔ 블랙리스트에 등록된 사용자입니다.")
                st.info("관리자에게 문의하세요.")
                return

        # 사용자 정보 표시
        st.markdown(f"""
        - **닉네임**: {user.get("nickname", "Unknown")}
        - **사령관번호**: {user.get("commander_id", "N/A")}
        - **서버**: {user.get("server", "N/A")}
        - **연맹**: {user.get("alliance", "없음") if user.get("alliance") else "없음"}
        """)

        # 내 예약 현황
        my_reservations = db.list_reservations(user_id=user["id"])

        if my_reservations:
            latest_reservation = my_reservations[0]

            st.markdown("---")
            st.markdown("### 📊 내 최신 예약 현황")

            # 대기자 정보
            if latest_reservation.get("status") == "waitlisted":
                waitlist_order = latest_reservation.get("waitlist_order")
                waitlist_position = latest_reservation.get("waitlist_position")
                st.warning(f"🔵 대기자 명단에 등록되었습니다.")
                st.info(f"대기자 순번: {waitlist_order}번")
                st.info(f"현재 순번: {waitlist_position}번")

                # 예상 대기 시간 (하루에 1명씩 빠짐는 것으로 가정)
                if waitlist_position > 0:
                    expected_days = waitlist_position
                    st.info(f"예상 대기 시간: 약 {expected_days}일")

            elif latest_reservation.get("status") == "pending":
                st.success("🟡 예약 승인 대기중입니다.")
                st.info("관리자가 승인하면 참여 가능합니다.")

            elif latest_reservation.get("status") == "approved":
                st.success("🟢 예약이 승인되었습니다!")
                st.info(f"승인일시: {latest_reservation.get('approved_at', 'N/A')}")

            elif latest_reservation.get("status") == "rejected":
                st.error("🔴 예약이 거절되었습니다.")
                if latest_reservation.get("notes"):
                    st.text(f"비고: {latest_reservation['notes']}")

            elif latest_reservation.get("status") == "cancelled":
                st.info("⚪ 예약이 취소되었습니다.")

            st.markdown(f"신청일시: {latest_reservation['created_at']}")

            # 선착순 정보
            st.markdown("---")
            st.markdown("### ⏰ 선착순 정보")

            # 내 순위 계산
            my_order, is_within = get_my_order(user["id"])

            if my_order and is_within:
                st.success(f"현재 순위: {my_order}번 (정원 내)")
            elif my_order:
                st.warning(f"현재 순위: {my_order}번 (정원 외)")
            else:
                st.info("아직 예약 내역이 없습니다.")

        # 새로운 예약 안내
        if not my_reservations:
            st.info("아직 예약 내역이 없습니다.")
            st.markdown("---")

            if not status["is_session_active"]:
                st.markdown("### 📝 예약 신청")
            else:
                st.warning(
                    "⚠️ 현재 회차가 마감되었습니다. 예약은 대기자 명단에 등록됩니다."
                )

            if st.button("예약하러 가기", use_container_width=True, type="primary"):
                st.session_state["page"] = "reservation"
                st.rerun()

    else:
        st.markdown("### 👋 환영합니다!")
        st.markdown("DaWn Dice Party에 오신 것을 환영합니다!")
        st.markdown("---")

        # 주요 안내
        st.markdown("### 📋 주요 안내")

        st.markdown("""
        - **선착순 예약**: 먼저 예약한 분들 우선 참여
        - **최대 참여자**: 회차별 180명
        - **대기자 시스템**: 정원 초과 시 대기자 명단 자동 등록
        - **사령관번호**: 10자리 숫자로 가입 가능

        - **비밀번호**: 최소 8자 이상
        - **블랙리스트**: 블랙리스트에 등록된 사령관번호는 예약 불가
        - **Google Sheets**: 외부 블랙리스트와 통합

        ## 회차별 시스템

        - 회차별로 예약 마감 시 대기자 명단으로 자동 전환
        - 기존 참여자는 기존 회차 우선 예약 가능
        - 외부 참여자는 새 회차에 예약 가능
        - 회차별 회차 마감 시에는 '회차 마감' 메시지 표시

        ## 우선순위

        **1순위**: 기존 참여자 (이전 회차 참여자)
        - 정원 외: 가입 순서대로 예약 가능

        **2순위**: 회차별 선착순 예약
        - 예약 순서대로 참여 가능

        ## 예약 마감 시

        - 예약이 마감되면 '[N회차] 예약 마감 - 대기순번 등록만 가능' 메시지
        - 대기자 순번은 예약 순서대로 배정됩니다.
        """)

        st.markdown("---")

        # 공지사항 표시
        st.markdown("### 📢 공지사항")

        # 최신 공지사항 표시 (최대 3개, 상단 고정 우선)
        announcements = db.list_announcements(is_active=True, limit=5)

        # 상단 고정 공지 우선
        pinned = [a for a in announcements if a.get("is_pinned")]
        regular = [a for a in announcements if not a.get("is_pinned")]

        display_announcements = (pinned + regular[:3]) if regular else pinned

        if display_announcements:
            for ann in display_announcements:
                # 카테고리 뱃지
                category_badge = {"공지": "📢", "안내": "ℹ️", "이벤트": "🎉"}

                badge = category_badge.get(ann.get("category", "공지"), "📢")

                # 상단 고정 표시
                pin_indicator = " 📌 상단고정" if ann.get("is_pinned") else ""

                with st.expander(f"{badge} {ann['title']}{pin_indicator}"):
                    st.markdown(ann["content"])

                    st.markdown(
                        f"작성자: {ann.get('author_name', 'Unknown')} | 작성일: {ann['created_at'][:19]}"
                    )
        else:
            st.info("등록된 공지사항이 없습니다.")

    # 마크다운
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>©2026 DaWn Dice Party by 엔티티</div>",
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
