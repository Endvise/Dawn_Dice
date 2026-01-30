#!/usr/bin/env python3
"""
관리자 예약 관리 페이지
"""

import streamlit as st
import database as db
import auth


def show():
    """관리자 예약 관리 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("📋 예약 관리")
    st.markdown("---")

    # 통계
    all_reservations = db.list_reservations()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("전체 예약", len(all_reservations))

    with col2:
        pending = len([r for r in all_reservations if r["status"] == "pending"])
        st.metric("대기중", pending)

    with col3:
        approved = len([r for r in all_reservations if r["status"] == "approved"])
        st.metric("승인됨", approved)

    with col4:
        rejected = len([r for r in all_reservations if r["status"] == "rejected"])
        st.metric("거절됨", rejected)

    with col5:
        blacklisted = len([r for r in all_reservations if r.get("is_blacklisted")])
        st.metric("블랙리스트", blacklisted)

    st.markdown("---")

    # 필터
    st.markdown("### 🔍 필터")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "상태 필터", ["전체", "대기중", "승인됨", "거절됨", "취소됨"]
        )

    with col2:
        blacklist_filter = st.selectbox(
            "블랙리스트 필터", ["전체", "블랙리스트", "정상"]
        )

    with col3:
        search_term = st.text_input("검색 (닉네임/사령관번호)")

    st.markdown("---")

    # 예약 목록
    filtered_reservations = []

    for res in all_reservations:
        # 상태 필터
        if status_filter != "전체":
            status_map = {
                "대기중": "pending",
                "승인됨": "approved",
                "거절됨": "rejected",
                "취소됨": "cancelled",
            }

            if res["status"] != status_map[status_filter]:
                continue

        # 블랙리스트 필터
        if blacklist_filter == "블랙리스트" and not res.get("is_blacklisted"):
            continue

        if blacklist_filter == "정상" and res.get("is_blacklisted"):
            continue

        # 검색 필터
        if search_term:
            search_lower = search_term.lower()
            if search_lower not in res["nickname"].lower() and search_lower not in str(
                res["commander_id"]
            ):
                continue

        filtered_reservations.append(res)

    st.markdown(f"### 📋 예약 목록 ({len(filtered_reservations)}건)")

    if filtered_reservations:
        for res in filtered_reservations:
            # 상태 색상
            status_color = {
                "pending": "🟡",
                "approved": "🟢",
                "rejected": "🔴",
                "cancelled": "⚪",
            }

            status_label = (
                status_color.get(res["status"], "❓") + " " + res["status"].upper()
            )

            # 블랙리스트 표시
            blacklist_warning = " ⛔ 블랙리스트" if res.get("is_blacklisted") else ""

            # 예약 카드
            with st.expander(
                f"{status_label}{blacklist_warning} - {res['created_at'][:19]} (ID: {res['id']})"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **닉네임**: {res["nickname"]}
                    **사령관번호**: {res["commander_id"]}
                    **서버**: {res["server"]}
                    **연맹**: {res["alliance"] if res["alliance"] else "없음"}
                    **신청자**: {res.get("user_nickname", res.get("user_role", "Unknown"))}
                    **신청일시**: {res["created_at"]}
                    **상태**: {res["status"]}
                    """)

                    if res.get("approved_at"):
                        st.markdown(f"**승인일시**: {res['approved_at']}")

                    if res.get("notes"):
                        st.text(f"**비고**: {res['notes']}")

                    if res.get("is_blacklisted"):
                        st.warning(
                            f"⛔ **블랙리스트**: {res.get('blacklist_reason', 'N/A')}"
                        )

                with col2:
                    # 액션 버튼
                    st.markdown("### 액션")

                    if res["status"] == "pending":
                        col_a1, col_a2 = st.columns(2)

                        with col_a1:
                            if st.button(
                                "승인",
                                key=f"approve_{res['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    db.update_reservation_status(
                                        res["id"], "approved", user["id"]
                                    )
                                    st.success("✓ 승인되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"승인 중 오류가 발생했습니다: {e}")

                        with col_a2:
                            if st.button(
                                "거절",
                                key=f"reject_{res['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    db.update_reservation_status(
                                        res["id"], "rejected", user["id"]
                                    )
                                    st.success("✓ 거절되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"거절 중 오류가 발생했습니다: {e}")

                    elif res["status"] == "approved":
                        if st.button(
                            "승인 취소",
                            key=f"cancel_approval_{res['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.update_reservation_status(res["id"], "pending", None)
                                st.success("✓ 승인이 취소되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"취소 중 오류가 발생했습니다: {e}")

                    # 삭제 버튼 (마스터만)
                    if is_master:
                        if st.button(
                            "삭제",
                            key=f"delete_{res['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            if st.confirm("정말 이 예약을 삭제하시겠습니까?"):
                                try:
                                    db.delete_reservation(res["id"])
                                    st.success("✓ 삭제되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {e}")

                    # 블랙리스트 추가 버튼
                    if not res.get("is_blacklisted"):
                        if st.button(
                            "블랙리스트 추가",
                            key=f"blacklist_{res['id']}",
                            use_container_width=True,
                        ):
                            reason = st.text_input(
                                "블랙리스트 사유", key=f"reason_{res['id']}"
                            )
                            if st.button(
                                "추가 확인",
                                key=f"add_blacklist_{res['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    db.add_to_blacklist(
                                        commander_id=res["commander_id"],
                                        nickname=res["nickname"],
                                        reason=reason if reason else "관리자 추가",
                                        added_by=user["id"],
                                    )
                                    st.success("✓ 블랙리스트에 추가되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"추가 중 오류가 발생했습니다: {e}")

    else:
        st.info("표시할 예약이 없습니다.")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 관리자 안내

    - **대기중**: 승인 또는 거절 가능
    - **승인됨**: 승인 취소 가능
    - **거절됨/취소됨**: 상태 변경 불가
    - **블랙리스트**: 자동으로 표시됨

    마스터 계정만 예약을 삭제할 수 있습니다.
    """)
