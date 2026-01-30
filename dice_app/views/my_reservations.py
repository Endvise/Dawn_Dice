#!/usr/bin/env python3
"""
내 예약 현황 페이지
"""

import streamlit as st
import database as db
import auth


def show():
    """내 예약 현황 페이지 표시"""
    # 로그인 확인
    auth.require_login()

    user = auth.get_current_user()

    st.title("📊 내 예약 현황")
    st.markdown("---")

    # 통계
    my_reservations = db.list_reservations(user_id=user["id"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("전체 예약", len(my_reservations))

    with col2:
        pending = len([r for r in my_reservations if r["status"] == "pending"])
        st.metric("대기중", pending)

    with col3:
        approved = len([r for r in my_reservations if r["status"] == "approved"])
        st.metric("승인됨", approved)

    with col4:
        rejected = len([r for r in my_reservations if r["status"] == "rejected"])
        st.metric("거절됨", rejected)

    st.markdown("---")

    # 필터
    st.markdown("### 🔍 필터")

    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "상태 필터", ["전체", "대기중", "승인됨", "거절됨", "취소됨"]
        )

    with col2:
        blacklist_filter = st.selectbox(
            "블랙리스트 필터", ["전체", "블랙리스트", "정상"]
        )

    st.markdown("---")

    # 예약 목록
    filtered_reservations = []

    for res in my_reservations:
        # 대기자 순번 표시
        waitlist_info = ""
        if res.get("status") == "waitlisted":
            waitlist_order = res.get("waitlist_order")
            waitlist_position = res.get("waitlist_position")
            waitlist_info = (
                f" (대기자: {waitlist_order}번 / 현재 순번: {waitlist_position}번)"
            )

        # 예약 카드
        with st.expander(
            f"{status_label}{waitlist_info} - {res['created_at'][:19]} (ID: {res['id']})"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **닉네임**: {res["nickname"]}
                **사령관번호**: {res["commander_id"]}
                **서버**: {res["server"]}
                **연맹**: {res["alliance"] if res["alliance"] else "없음"}
                **신청일시**: {res["created_at"]}
                **상태**: {res["status"]}
                """)

                if res.get("approved_at"):
                    st.markdown(f"**승인일시**: {res['approved_at']}")

                if res.get("waitlist_order"):
                    st.info(f"🔵 대기자 순번: {res.get('waitlist_order')}번")

                if res.get("notes"):
                    st.text(f"**비고**: {res['notes']}")

                if res.get("is_blacklisted"):
                    st.warning(
                        f"⚠️ **블랙리스트**: {res.get('blacklist_reason', 'N/A')}"
                    )

            with col2:
                # 취소 버튼 (대기중일 때만)
                if res["status"] == "pending":
                    if st.button(
                        "취소하기",
                        key=f"cancel_{res['id']}",
                        use_container_width=True,
                    ):
                        try:
                            db.cancel_reservation(res["id"])
                            st.success("✓ 예약이 취소되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"취소 중 오류가 발생했습니다: {e}")

                # 승인자 정보
                if res.get("approved_by"):
                    approver = db.get_user_by_id(res["approved_by"])
                    if approver:
                        st.info(
                            f"승인자: {approver.get('nickname', approver.get('username', 'Unknown'))}"
                        )

    else:
        st.info("표시할 예약이 없습니다.")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 안내

    - **대기중**: 관리자가 승인 대기 중
    - **승인됨**: 예약이 승인됨
    - **거절됨**: 관리자가 거절함
    - **취소됨**: 사용자가 직접 취소함

    블랙리스트에 등록된 사령관번호는 예약이 불가능합니다.
    """)
