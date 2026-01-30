#!/usr/bin/env python3
"""
회차별 이벤트 세션 관리 페이지
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from datetime import datetime, date, timedelta


def show():
    """회차별 이벤트 세션 관리 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("🎲 회차별 이벤트 세션 관리")
    st.markdown("---")

    # 현재 활성화된 회차 확인
    current_session = get_active_session()

    if current_session:
        st.info(
            f"현재 활성화된 회차: **{current_session['session_number']}회차** ({current_session['session_name']})"
        )
        st.warning(
            "현재 회차가 활성화되어 있습니다. 새 회차를 생성하려면 먼저 현재 회차를 비활성화하세요."
        )
    else:
        st.success("현재 활성화된 회차가 없습니다. 새 회차를 생성할 수 있습니다.")

    st.markdown("---")

    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📋 회차 목록", "➕ 회차 생성", "⚙️ 설정"])

    # 탭 1: 회차 목록
    with tab1:
        st.markdown("### 📋 회차 목록")

        # 회차 목록 불러오기
        sessions = get_all_sessions()

        if sessions:
            for session in sessions:
                # 활성화 상태 뱃지
                if session["is_active"]:
                    status_badge = "✅ 활성화"
                    status_color = "success"
                else:
                    status_badge = "⏳ 비활성"
                    status_color = "info"

                # 참여자 수 계산
                participant_count = get_participant_count(session["id"])
                approved_count = get_approved_reservation_count(session["id"])

                with st.expander(
                    f"{status_badge} {session['session_number']}회차 - {session['session_name']}"
                ):
                    st.markdown(f"""
                    **회차명**: {session["session_name"]}
                    **회차 날짜**: {session["session_date"]}
                    **최대 참여자**: {session["max_participants"]}명
                    **참여자 수**: {participant_count}명 (기존) + {approved_count}명 (예약) = {participant_count + approved_count}명
                    **생성자**: {session.get("creator_name", "Unknown")}
                    **생성일시**: {session["created_at"]}
                    """)

                    if (
                        participant_count + approved_count
                        >= session["max_participants"]
                    ):
                        st.error(
                            "⛔ 회차가 꽉 찼습니다! 새 예약은 대기자 명단에 등록됩니다."
                        )
                    else:
                        remaining = session["max_participants"] - (
                            participant_count + approved_count
                        )
                        st.success(f"✅ 남은 자리: {remaining}명")

                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        st.markdown("### 액션")

                        if session["is_active"]:
                            # 활성화된 회차
                            if st.button(
                                "비활성화",
                                key=f"deactivate_{session['id']}",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    f"{session['session_number']}회차를 비활성화하시겠습니까?"
                                ):
                                    update_session_active(session["id"], False)
                                    st.success("✓ 회차가 비활성화되었습니다.")
                                    st.rerun()
                        else:
                            # 비활성화된 회차
                            if st.button(
                                "활성화",
                                key=f"activate_{session['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                # 먼저 다른 활성화된 회차가 있는지 확인
                                other_active = get_active_session()
                                if other_active and other_active["id"] != session["id"]:
                                    st.error(
                                        f"⛔ 다른 회차({other_active['session_number']}회차)가 활성화되어 있습니다. 먼저 비활성화해주세요."
                                    )
                                else:
                                    update_session_active(session["id"], True)
                                    st.success(
                                        f"✓ {session['session_number']}회차가 활성화되었습니다."
                                    )
                                    st.rerun()

                            # 마스터만 삭제 가능
                            if is_master:
                                if st.button(
                                    "삭제",
                                    key=f"delete_{session['id']}",
                                    type="secondary",
                                    use_container_width=True,
                                ):
                                    if st.confirm(
                                        f"정말 {session['session_number']}회차를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
                                    ):
                                        delete_session(session["id"])
                                        st.success("✓ 회차가 삭제되었습니다.")
                                        st.rerun()

                    with col2:
                        st.markdown("### 📊 예약 현황")

                        # 회차별 예약 목록
                        session_reservations = get_session_reservations(session["id"])

                        st.metric("전체 예약", f"{len(session_reservations)}건")

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
                        - 대기중: {pending}건
                        - 승인됨: {approved}건
                        - 대기자: {waitlisted}명
                        """)

                    with col3:
                        st.markdown("### 👥 참여자")

                        # 참여자 목록
                        participants = get_session_participants(session["id"])

                        if participants:
                            for p in participants[:5]:  # 처음 5개만 표시
                                st.text(f"- {p['nickname']} ({p.get('igg_id', 'N/A')})")

                            if len(participants) > 5:
                                st.text(f"... 외 {len(participants) - 5}명")
                        else:
                            st.info("참여자가 없습니다.")
        else:
            st.info("등록된 회차가 없습니다.")

    # 탭 2: 회차 생성
    with tab2:
        st.markdown("### ➕ 회차 생성")

        if current_session:
            st.error("현재 활성화된 회차가 있어 새 회차를 생성할 수 없습니다.")
            return

        col1, col2 = st.columns([1, 2])

        with col1:
            # 폼
            session_number = st.number_input(
                "회차 번호", min_value=1, step=1, value=get_next_session_number()
            )

            session_name = st.text_input("회차명", placeholder="예: 260128 주사위 파티")

            # 날짜 선택
            today = date.today()
            min_date = today + timedelta(days=1)  # 내일부터
            session_date = st.date_input(
                "회차 날짜", min_value=min_date, value=min_date
            )

            max_participants = st.number_input(
                "최대 참여자", min_value=1, value=180, step=10
            )

        with col2:
            st.markdown("### 💡 안내")

            st.markdown("""
            - **회차 번호**: 자동 증가 (가능한 번호)
            - **회차명**: 예: "260128 주사위 파티"
            - **회차 날짜**: 이벤트 진행 예정일
            - **최대 참여자**: 기본 180명

            **회차 활성화**:
            - 생성 시 자동 활성화됩니다.
            - 새 회차 생성 시 기존 회차는 자동 비활성화됩니다.
            - 활성화된 회차만 예약 신청 가능합니다.

            **우선순위**:
            - 1순위: 기존 참여자 (이전 회차 참여자)
            - 2순위: 외부 참여자 (새로 가입)
            """)

        # 생성 버튼
        st.markdown("---")
        if st.button("회차 생성", type="primary", use_container_width=True):
            if not session_name:
                st.error("회차명을 입력해주세요.")
                return

            try:
                create_session(
                    session_number=session_number,
                    session_name=session_name,
                    session_date=session_date,
                    max_participants=max_participants,
                    created_by=user["id"],
                )

                st.success(f"✓ {session_number}회차가 생성되었습니다.")
                st.info(f"{session_name} 예약을 시작할 수 있습니다.")
                st.rerun()

            except Exception as e:
                st.error(f"생성 중 오류가 발생했습니다: {e}")

    # 탭 3: 설정
    with tab3:
        st.markdown("### ⚙️ 회차 설정")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### 기존 참여자 우선권")

            st.info("""
            **우선순위 설정**:
            
            **1순위**: 기존 참여자 우선
            - 이전 회차 참여자는 새 회차 예약 시 우선권을 갖습니다.
            - 참여자 기록이 있는 사용자: 우선 예약 가능
            - 참여자 기록이 없는 사용자: 대기자 대기

            **2순위**: 외부 참여자
            - 새로 가입한 사용자는 참여자 기록이 없습니다.
            - 기존 참여자 예약 후 남은 자리에 예약 가능.
            """)

        with col2:
            st.markdown("### 대기자 시스템")

            st.info("""
            **대기자 시스템**:

            - 회차 정원: {db.MAX_PARTICIPANTS}명
            - 정원 초과 시: 대기자 명단 등록
            - 대기자 순번: 선착순으로 부여
            - 승인 시: 대기자 순서대로 승인 가능

            **주요**:
            - 기존 참여자가 먼저 채워지는 자리입니다.
            - 남은 자리는 외부 참여자 순서로 채워집니다.
            """)

        st.markdown("---")
        st.markdown("### 📢 공지사항 작성 안내")

        st.info("""
        **회차 마감 시 공지사항 작성**:

        1. 관리자가 회차 마감 시점을 확인합니다.
        2. "📢 공지사항 관리" 페이지에서 안내사항을 작성합니다.
        3. 홈페이지에서 사용자들이 볼 수 있도록 표시됩니다.
        4. 예: "[2회차] 예약 마감 - 1월 31일 자정 확정"

        **공지사항 내용 예시**:
        ```markdown
        # [2회차] 예약 마감 안내

        안녕하세요! 2회차 예약이 마감되었습니다.

        ## 📅 일정
        - **자정 확정**: 1월 31일 오후 8시
        - **장소**: 온라인 디스코드

        ## ⚠️ 중요
        - 정원: 180명
        - 예약 시간: 내일 오후 8시 마감
        - 선착순 예약: 먼저 예약한 분들 우선

        ## 📋 우선순위
        1. 기존 참여자 (1회차 참여자)
        2. 외부 참여자 (새로 가입)
        ```

        **회차 시작 전 공지**:
        - 회차 시작 안내
        - 참여 방법 안내
        - 주의사항 전달
        """)


# ===== Helper Functions =====


def get_all_sessions():
    """모든 회차 목록을 반환합니다."""
    results = execute_query(
        """
        SELECT s.*, u.nickname as creator_name
        FROM event_sessions s
        LEFT JOIN users u ON s.created_by = u.id
        ORDER BY s.session_number DESC
        """,
        fetch="all",
    )
    return [dict(row) for row in results]


def get_active_session():
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


def get_next_session_number():
    """다음 회차 번호를 반환합니다."""
    result = execute_query(
        "SELECT MAX(session_number) as max_number FROM event_sessions", fetch="one"
    )
    return (result.get("max_number", 0) if result else 0) + 1


def get_participant_count(session_id: int) -> int:
    """회차별 기존 참여자 수를 반환합니다."""
    session = execute_query(
        "SELECT session_name FROM event_sessions WHERE id = ?",
        (session_id,),
        fetch="one",
    )

    if not session:
        return 0

    event_name = session["session_name"]
    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE event_name = ? AND completed = 1",
        (event_name,),
        fetch="one",
    )
    return result.get("count", 0) if result else 0


def get_approved_reservation_count(session_id: int) -> int:
    """회차별 승인된 예약 수를 반환합니다."""
    # 현재 구현에서는 예약 테이블에 session_id가 없으니 전체 승인된 예약 반환
    # 추후 session_id 추가 시 수정 필요
    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    return result.get("count", 0) if result else 0


def get_session_reservations(session_id: int):
    """회차별 예약 목록을 반환합니다."""
    # 현재 구현에서는 모든 예약 반환
    # 추후 session_id 추가 시 필터링 필요
    return db.list_reservations()


def get_session_participants(session_id: int):
    """회차별 참여자 목록을 반환합니다."""
    session = execute_query(
        "SELECT session_name FROM event_sessions WHERE id = ?",
        (session_id,),
        fetch="one",
    )

    if not session:
        return []

    event_name = session["session_name"]
    results = execute_query(
        "SELECT * FROM participants WHERE event_name = ? ORDER BY number",
        (event_name,),
        fetch="all",
    )
    return [dict(row) for row in results]


def update_session_active(session_id: int, is_active: bool):
    """회차 활성화 상태를 업데이트합니다."""
    execute_query(
        "UPDATE event_sessions SET is_active = ? WHERE id = ?",
        (1 if is_active else 0, session_id),
    )


def delete_session(session_id: int):
    """회차를 삭제합니다."""
    execute_query("DELETE FROM event_sessions WHERE id = ?", (session_id,))


def create_session(
    session_number: int,
    session_name: str,
    session_date: date,
    max_participants: int,
    created_by: int,
):
    """새 회차를 생성합니다."""
    # 기존 활성화된 회차 비활성화
    execute_query("UPDATE event_sessions SET is_active = 0")

    # 새 회차 생성
    execute_query(
        """
        INSERT INTO event_sessions (session_number, session_name, session_date, max_participants, created_by)
        VALUES (?, ?, ?, ?, ?)
    """,
        (session_number, session_name, session_date, max_participants, created_by),
    )
