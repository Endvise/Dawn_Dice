#!/usr/bin/env python3
"""
예약 신청 페이지
"""

import streamlit as st
import database as db
import auth
from database import execute_query


def show():
    """예약 신청 페이지 표시"""
    # 로그인 확인
    auth.require_login()

    # 사용자 정보
    user = auth.get_current_user()

    # 블랙리스트 체크
    if user.get("commander_id"):
        blacklisted = db.check_blacklist(user["commander_id"])

        if blacklisted:
            st.error(
                f"⛔ 블랙리스트에 등록되어 있습니다. (사유: {blacklisted.get('reason', 'N/A')})"
            )
            st.info("관리자에게 문의하세요.")
            return

    st.title("📝 예약 신청")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # 사용자 정보 표시
        st.markdown("### 👤 사용자 정보")
        st.info(f"""
        - **닉네임**: {user.get("nickname", "Unknown")}
        - **사령관번호**: {user.get("commander_id", "N/A")}
        - **서버**: {user.get("server", "N/A")}
        - **연맹**: {user.get("alliance", "N/A") if user.get("alliance") else "없음"}
        """)

        st.markdown("---")

        # 예약 신청 폼
        st.markdown("### 🎲 예약 정보 입력")

        # 서버 입력 (자유 입력)
        server = st.text_input(
            "서버", value=user.get("server", ""), placeholder="예: #095 woLF"
        )

        # 연맹 (선택사항, 변경 가능)
        alliance = st.text_input(
            "연맹이름",
            value=user.get("alliance", ""),
            placeholder="소속 연맹이 있다면 입력하세요",
        )

        # 현재 참여자 수 표시
        participants_count = execute_query(
            "SELECT COUNT(*) as count FROM participants WHERE completed = 1",
            fetch="one",
        ).get("count", 0)

        approved_count = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
            fetch="one",
        ).get("count", 0)

        total_count = participants_count + approved_count

        st.info(f"현재 참여자 수: {total_count} / {db.MAX_PARTICIPANTS}명")

        if total_count >= db.MAX_PARTICIPANTS:
            st.warning("⚠️ 참여자 수가 꽉 찼습니다. 예약은 대기자 명단에 등록됩니다.")

        # 비고
        notes = st.text_area(
            "비고", placeholder="추가로 전달할 사항이 있다면 입력하세요", height=100
        )

        st.markdown("---")

        # 버튼 영역
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

        with col_btn2:
            if st.button("예약 신청하기", use_container_width=True, type="primary"):
                # 예약 생성
                try:
                    reservation_id = db.create_reservation(
                        user_id=user["id"],
                        nickname=user.get("nickname", ""),
                        commander_id=user.get("commander_id", ""),
                        server=server,
                        alliance=alliance if alliance else None,
                        notes=notes if notes else None,
                    )

                    # 블랙리스트 경고
                    reservation = db.get_reservation_by_id(reservation_id)

                    if reservation and reservation.get("status") == "waitlisted":
                        waitlist_order = reservation.get("waitlist_order")
                        st.warning(
                            f"⚠️ 예약이 대기자 명단에 등록되었습니다. 대기자 순번: {waitlist_order}번"
                        )
                    elif reservation and reservation.get("status") == "pending":
                        st.success(
                            f"✓ 예약 신청이 완료되었습니다! (예약 번호: {reservation_id})"
                        )

                    if reservation and reservation.get("is_blacklisted"):
                        st.warning(
                            f"⚠️ 블랙리스트에 등록된 사령관번호입니다. (사유: {reservation.get('blacklist_reason', 'N/A')})"
                        )

                except Exception as e:
                    st.error(f"예약 신청 중 오류가 발생했습니다: {e}")

        # 안내 메시지
        st.markdown("---")
        st.markdown("""
        ### 💡 예약 안내

        - 예약 신청 후 관리자가 승인해야 합니다.
        - 블랙리스트에 등록된 사령관번호는 예약이 불가능합니다.
        - 예약 상태는 "내 예약 현황" 페이지에서 확인할 수 있습니다.
        - 서버/연맹은 예약 시점의 정보로 저장됩니다.
        """)

        # 내 예약 현황 미리보기
        st.markdown("---")
        st.markdown("### 📊 최근 예약 현황")

        my_reservations = db.list_reservations(user_id=user["id"], limit=5)

        if my_reservations:
            for res in my_reservations:
                status_color = {
                    "pending": "🟡",
                    "approved": "🟢",
                    "rejected": "🔴",
                    "cancelled": "⚪",
                }

                status_label = (
                    status_color.get(res["status"], "❓") + " " + res["status"].upper()
                )

                st.markdown(f"""
                **{status_label}** - {res["created_at"]}
                - 서버: {res["server"]}
                - 연맹: {res["alliance"] if res["alliance"] else "없음"}
                """)

                if res.get("is_blacklisted"):
                    st.warning(f"⚠️ 블랙리스트: {res.get('blacklist_reason', 'N/A')}")

                if res.get("notes"):
                    st.text(f"비고: {res['notes']}")

                st.markdown("---")
        else:
            st.info("아직 예약 내역이 없습니다.")
