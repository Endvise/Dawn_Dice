#!/usr/bin/env python3
"""
Admin Reservation Settings Page
"""

import streamlit as st
import database as db
from datetime import datetime


def show_reservation_settings():
    """Reservation Settings Admin Page."""
    st.title("⚙️ 예약 설정 관리")

    # 현재 활성화된 세션
    session = db.get_active_session()
    if not session:
        st.warning("📋 활성화된 세션이 없습니다.")

        # 새 세션 생성 옵션
        with st.expander("새 세션 생성"):
            st.info("회차별 세션 관리 페이지에서 새 세션을 생성하세요.")

        return

    session_id = session.get("id", "")
    session_name = session.get(
        "session_name", f"제 {session.get('session_number', 1)}회"
    )

    # 예약 상태 관리
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 예약 상태")
        is_open = session.get("is_reservation_open", False)

        if is_open:
            st.success("🔓 **예약 오픈됨**")
            if st.button("🔒 예약 마감하기", type="primary"):
                db.update_session_active(session_id, False)
                st.rerun()
        else:
            st.error("🔒 **예약 마감됨**")
            if st.button("🔓 예약 오픈하기", type="primary"):
                db.update_session_active(session_id, True)
                st.rerun()

    with col2:
        st.subheader("⏰ 예약 시간 설정")

        # 시간 입력
        col_time1, col_time2 = st.columns(2)
        with col_time1:
            open_time = st.text_input(
                "예약 오픈 시간",
                value=session.get("reservation_open_time", "") or "",
                placeholder="YYYY-MM-DD HH:MM",
                help="예: 2026-02-15 12:00",
            )
        with col_time2:
            close_time = st.text_input(
                "예약 마감 시간",
                value=session.get("reservation_close_time", "") or "",
                placeholder="YYYY-MM-DD HH:MM",
                help="예: 2026-02-20 23:59",
            )

        if st.button("💾 시간 저장"):
            try:
                db.update(
                    session_id,
                    {
                        "reservation_open_time": open_time,
                        "reservation_close_time": close_time,
                    },
                    {"id": f"eq.{session_id}"},
                )
                st.success("✅ 저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

    st.markdown("---")

    # 현재 예약 현황
    st.subheader("📈 현재 예약 현황")

    # 통계 계산
    approved_count = db.get_approved_reservation_count(session_id)
    pending_count = len(db.list_reservations(status="pending"))
    waitlisted_count = len(db.list_reservations(status="waitlisted"))
    rejected_count = len(db.list_reservations(status="rejected"))
    max_participants = session.get("max_participants", 180)

    # 통계 카드
    col_stat1, col_stat2, col_stat3, col_stat4, col_stat5 = st.columns(5)
    col_stat1.metric(
        "승인됨",
        approved_count,
        f"{max_participants - approved_count}남음",
        delta_color="normal",
    )
    col_stat2.metric("대기 중", pending_count)
    col_stat3.metric("대기자", waitlisted_count)
    col_stat4.metric("거절됨", rejected_count)
    col_stat5.metric("정원", f"{approved_count}/{max_participants}")

    # 진행률 바
    progress = min(approved_count / max_participants, 1.0)
    st.progress(progress)

    # 상태에 따른 색상 변화
    if approved_count >= max_participants:
        st.error("🚨 정원이 초과되었습니다! 추가 예약을 받으면 대기로 처리됩니다.")
    elif approved_count >= max_participants * 0.9:
        st.warning("⚠️ 정원이 거의 마감되었습니다.")
    else:
        st.success("🎉 예약이 원활히 진행되고 있습니다.")

    # 예약 가능 여부 UI 제어 (외부인에게 보여줄 내용)
    st.markdown("---")
    st.subheader("🌐 외부인 예약 현황 UI")

    # 외부인 예약 가능 여부 설정
    enable_public_view = st.checkbox(
        "외부인에게 예약 현황 보여주기",
        value=session.get("enable_public_view", False),
        help="체크하면 비로그인 사용자도 예약 현황을 확인할 수 있습니다.",
    )

    if st.button("💾 설정 저장"):
        try:
            db.update(
                session_id,
                {"enable_public_view": enable_public_view},
                {"id": f"eq.{session_id}"},
            )
            st.success("✅ 설정 저장됨!")
        except Exception as e:
            st.error(f"설정 저장 실패: {e}")

    # 예약 현황 페이지 링크
    if enable_public_view:
        st.info(
            "📎 예약 현황 페이지: `views/public_status.py`를 통해 외부에 공개됩니다."
        )


def show_reservation_list():
    """Show reservation list with filters."""
    st.title("📋 예약자 명단 관리")

    # 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "상태 필터",
            ["all", "pending", "approved", "rejected", "cancelled", "waitlisted"],
        )
    with col2:
        search = st.text_input("사령관번호/닉네임 검색")
    with col3:
        is_blacklisted = st.selectbox("블랙리스트", ["all", "yes", "no"])

    # 예약 목록 가져오기
    reservations = db.list_reservations()

    # 필터 적용
    if status_filter != "all":
        reservations = [r for r in reservations if r.get("status") == status_filter]

    if search:
        reservations = [
            r
            for r in reservations
            if search in str(r.get("commander_id", ""))
            or search in str(r.get("nickname", ""))
        ]

    if is_blacklisted != "all":
        is_bl = is_blacklisted == "yes"
        reservations = [r for r in reservations if r.get("is_blacklisted") == is_bl]

    # 결과 표시
    st.write(f"**총 {len(reservations)}명**")

    if reservations:
        # 테이블 형태로 표시
        import pandas as pd

        df = pd.DataFrame(reservations)

        # 표시할 컬럼 선택
        display_cols = [
            "nickname",
            "commander_id",
            "server",
            "alliance",
            "status",
            "is_blacklisted",
            "created_at",
        ]
        st.dataframe(df[display_cols], use_container_width=True)

        # 상세 정보 및 작업
        with st.expander("상세 작업"):
            selected = st.selectbox(
                "예약 선택",
                [f"{r['nickname']} ({r['commander_id']})" for r in reservations],
            )
            if selected:
                idx = [
                    f"{r['nickname']} ({r['commander_id']})" for r in reservations
                ].index(selected)
                res = reservations[idx]

                st.write("### 선택한 예약 정보")
                st.json(res)

                # 승인/거절 버튼
                col_approve, col_reject = st.columns(2)
                if res.get("status") == "pending":
                    if col_approve.button("✅ 승인"):
                        db.update_reservation_status(
                            res["id"], "approved", "current_user"
                        )
                        st.rerun()
                    if col_reject.button("❌ 거절"):
                        db.update_reservation_status(
                            res["id"], "rejected", "current_user"
                        )
                        st.rerun()


if __name__ == "__main__":
    tab1, tab2 = st.tabs(["⚙️ 예약 설정", "📋 예약자 명단"])
    with tab1:
        show_reservation_settings()
    with tab2:
        show_reservation_list()
