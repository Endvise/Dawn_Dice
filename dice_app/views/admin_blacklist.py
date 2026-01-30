#!/usr/bin/env python3
"""
관리자 블랙리스트 관리 페이지
"""

import streamlit as st
import database as db
import auth


def show():
    """블랙리스트 관리 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("🚫 블랙리스트 관리")
    st.markdown("---")

    # 통계
    local_blacklist = db.list_blacklist(is_active=True)
    total_blacklisted = len(local_blacklist)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("로컬 블랙리스트", f"{total_blacklisted}명")

    with col2:
        st.info("💡 Google Sheets 블랙리스트도 자동 체크됩니다.")

    st.markdown("---")

    # 탭
    tab1, tab2, tab3 = st.tabs(
        ["📋 블랙리스트 목록", "➕ 블랙리스트 추가", "📜 비활성화 목록"]
    )

    # 탭 1: 블랙리스트 목록
    with tab1:
        st.markdown("### 📋 활성화된 블랙리스트")

        if local_blacklist:
            for bl in local_blacklist:
                with st.expander(
                    f"🚫 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **사령관번호**: {bl["commander_id"]}
                        **닉네임**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                        **사유**: {bl["reason"] if bl["reason"] else "N/A"}
                        **추가일시**: {bl["added_at"]}
                        """)

                        # 추가자 정보
                        if bl.get("added_by"):
                            adder = db.get_user_by_id(bl["added_by"])
                            if adder:
                                st.info(
                                    f"추가자: {adder.get('nickname', adder.get('username', 'Unknown'))}"
                                )

                    with col2:
                        st.markdown("### 액션")

                        # 비활성화 버튼
                        if st.button(
                            "비활성화",
                            key=f"deactivate_{bl['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.remove_from_blacklist(bl["commander_id"])
                                st.success("✓ 블랙리스트에서 제거되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"제거 중 오류가 발생했습니다: {e}")
        else:
            st.info("활성화된 블랙리스트가 없습니다.")

    # 탭 2: 블랙리스트 추가
    with tab2:
        st.markdown("### ➕ 블랙리스트 추가")

        col1, col2 = st.columns([1, 2])

        with col1:
            commander_id = st.text_input("사령관번호", placeholder="10자리 숫자")

            # 중복 체크
            if commander_id:
                existing = db.check_blacklist(commander_id)
                if existing:
                    st.error(
                        f"⛔ 이미 블랙리스트에 등록되어 있습니다. (사유: {existing.get('reason', 'N/A')})"
                    )
                else:
                    st.success("✓ 새로운 사령관번호입니다.")

            nickname = st.text_input("닉네임", placeholder="선택사항")
            reason = st.text_area("블랙리스트 사유", placeholder="필수", height=100)

        with col2:
            st.markdown("### 💡 안내")

            st.markdown("""
            - **사령관번호**: 10자리 숫자 (필수)
            - **닉네임**: 선택사항
            - **사유**: 블랙리스트 등록 사유 (필수)

            블랙리스트에 등록된 사용자는:
            - 예약 신청 불가
            - 가입 불가
            - 기존 예약 자동 취소
            """)

        # 추가 버튼
        st.markdown("---")
        if st.button("블랙리스트에 추가", type="primary", use_container_width=True):
            if not commander_id:
                st.error("사령관번호를 입력해주세요.")
                return

            if not reason:
                st.error("블랙리스트 사유를 입력해주세요.")
                return

            try:
                db.add_to_blacklist(
                    commander_id=commander_id,
                    nickname=nickname if nickname else None,
                    reason=reason,
                    added_by=user["id"],
                )

                st.success(f"✓ {commander_id}님이 블랙리스트에 추가되었습니다.")

                # 기존 예약 체크
                affected_reservations = db.list_reservations()
                affected_count = len(
                    [
                        r
                        for r in affected_reservations
                        if r["commander_id"] == commander_id
                    ]
                )

                if affected_count > 0:
                    st.warning(f"⚠️ {affected_count}개의 예약이 영향을 받습니다.")

                st.rerun()

            except Exception as e:
                st.error(f"추가 중 오류가 발생했습니다: {e}")

    # 탭 3: 비활성화 목록
    with tab3:
        st.markdown("### 📜 비활성화된 블랙리스트")

        # 비활성화 목록 불러오기
        inactive_blacklist = db.list_blacklist(is_active=False)

        if inactive_blacklist:
            st.info(f"{len(inactive_blacklist)}명의 비활성화된 블랙리스트가 있습니다.")

            for bl in inactive_blacklist:
                with st.expander(
                    f"🔓 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **사령관번호**: {bl["commander_id"]}
                    **닉네임**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                    **사유**: {bl["reason"] if bl["reason"] else "N/A"}
                    **추가일시**: {bl["added_at"]}
                    """)

                    # 복원 버튼
                    if st.button(
                        "복원", key=f"restore_{bl['id']}", use_container_width=True
                    ):
                        # 복원은 is_active = 1로 업데이트
                        try:
                            execute_query(
                                """
                                UPDATE blacklist SET is_active = 1 WHERE id = ?
                            """,
                                (bl["id"],),
                            )

                            # 기존 예약들도 블랙리스트 제거
                            execute_query(
                                """
                                UPDATE reservations SET is_blacklisted = 0, blacklist_reason = NULL
                                WHERE commander_id = ?
                            """,
                                (bl["commander_id"],),
                            )

                            st.success("✓ 블랙리스트가 복원되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"복원 중 오류가 발생했습니다: {e}")

                    # 영구 삭제 버튼 (마스터만)
                    if is_master:
                        if st.button(
                            "영구 삭제",
                            key=f"permanent_delete_{bl['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                "정말 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
                            ):
                                try:
                                    execute_query(
                                        "DELETE FROM blacklist WHERE id = ?",
                                        (bl["id"],),
                                    )
                                    st.success("✓ 영구 삭제되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
        else:
            st.info("비활성화된 블랙리스트가 없습니다.")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 관리자 안내

    - **활성화**: 해당 사령관번호는 예약/가입 불가
    - **비활성화**: 일시적으로 차단 해제 (복원 가능)
    - **영구 삭제**: 완전히 삭제 (복원 불가)
    - **Google Sheets**: 외부 블랙리스트도 자동 체크됨

    마스터 계정만 영구 삭제가 가능합니다.
    """)

    # execute_query import 추가 필요
    from database import execute_query
