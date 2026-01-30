#!/usr/bin/env python3
"""
마스터 관리자 계정 관리 페이지
"""

import streamlit as st
import database as db
import auth


def show():
    """마스터 관리자 계정 관리 페이지 표시"""
    # 마스터 권한 확인
    auth.require_login(required_role="master")

    user = auth.get_current_user()

    st.title("👤 관리자 계정 관리")
    st.markdown("---")

    # 관리자 목록 불러오기
    admins = db.list_users(role="admin")

    # 통계
    total_admins = len(admins)
    active_admins = len([a for a in admins if a.get("is_active")])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("전체 관리자", f"{total_admins}명")

    with col2:
        st.metric("활성화된 관리자", f"{active_admins}명")

    st.markdown("---")

    # 탭
    tab1, tab2 = st.tabs(["📋 관리자 목록", "➕ 관리자 추가"])

    # 탭 1: 관리자 목록
    with tab1:
        st.markdown("### 📋 관리자 목록")

        if admins:
            for admin in admins:
                # 활성화 상태 뱃지
                status_badge = "✅" if admin.get("is_active") else "⏳"

                with st.expander(
                    f"{status_badge} {admin.get('username', 'Unknown')} - {admin.get('nickname', 'Unknown')}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **사용자명**: {admin.get("username", "Unknown")}
                        **닉네임**: {admin.get("nickname", "Unknown")}
                        **서버**: {admin.get("server", "N/A")}
                        **연맹**: {admin.get("alliance", "N/A") if admin.get("alliance") else "없음"}
                        **역할**: {admin.get("role", "Unknown")}
                        **활성화**: {"활성" if admin.get("is_active") else "비활성"}
                        **생성일시**: {admin.get("created_at", "N/A")}
                        **마지막 로그인**: {admin.get("last_login", "N/A") if admin.get("last_login") else "없음"}
                        """)

                        # 로그인 실패 횟수
                        if admin.get("failed_attempts", 0) > 0:
                            st.warning(f"⚠️ 로그인 실패: {admin['failed_attempts']}회")

                    with col2:
                        st.markdown("### 액션")

                        # 비밀번호 초기화
                        if st.button(
                            "비밀번호 초기화",
                            key=f"reset_pwd_{admin['id']}",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"{admin.get('username', 'Unknown')}의 비밀번호를 초기화하시겠습니까?"
                            ):
                                try:
                                    # 새로운 비밀번호 생성
                                    import secrets

                                    new_password = secrets.token_urlsafe(12)

                                    # 비밀번호 업데이트
                                    db.update_user(admin["id"], password=new_password)

                                    st.success(f"✓ 비밀번호가 초기화되었습니다.")
                                    st.code(
                                        f"새 비밀번호: {new_password}", language=None
                                    )
                                except Exception as e:
                                    st.error(f"초기화 중 오류가 발생했습니다: {e}")

                        # 활성화/비활성화
                        if admin.get("is_active"):
                            if st.button(
                                "비활성화",
                                key=f"deactivate_{admin['id']}",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    f"{admin.get('username', 'Unknown')}을 비활성화하시겠습니까?"
                                ):
                                    try:
                                        db.update_user(admin["id"], is_active=0)
                                        st.success("✓ 비활성화되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(
                                            f"비활성화 중 오류가 발생했습니다: {e}"
                                        )
                        else:
                            if st.button(
                                "활성화",
                                key=f"activate_{admin['id']}",
                                type="primary",
                                use_container_width=True,
                            ):
                                try:
                                    db.update_user(admin["id"], is_active=1)
                                    st.success("✓ 활성화되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"활성화 중 오류가 발생했습니다: {e}")

                        # 수정
                        if st.button(
                            "수정", key=f"edit_{admin['id']}", use_container_width=True
                        ):
                            st.session_state["edit_admin_id"] = admin["id"]
                            st.rerun()

                        # 삭제
                        if st.button(
                            "삭제",
                            key=f"delete_{admin['id']}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            if st.confirm(
                                f"정말 {admin.get('username', 'Unknown')}을 삭제하시겠습니까?"
                            ):
                                try:
                                    db.delete_user(admin["id"])
                                    st.success("✓ 삭제되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 중 오류가 발생했습니다: {e}")
        else:
            st.info("등록된 관리자가 없습니다.")

    # 탭 2: 관리자 추가
    with tab2:
        st.markdown("### ➕ 관리자 추가")

        col1, col2 = st.columns([1, 2])

        with col1:
            # 폼
            username = st.text_input(
                "사용자명", placeholder="영문/숫자", key="new_admin_username"
            )

            # 중복 체크
            if username:
                existing = db.get_user_by_username(username)
                if existing:
                    st.error(f"⛔ 이미 존재하는 사용자명입니다: {username}")
                else:
                    st.success("✓ 사용 가능한 사용자명입니다.")

            nickname = st.text_input(
                "닉네임", placeholder="필수", key="new_admin_nickname"
            )

            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="8자 이상",
                key="new_admin_password",
            )
            confirm_password = st.text_input(
                "비밀번호 확인", type="password", key="new_admin_confirm_password"
            )

            # 비밀번호 검증
            if password and confirm_password:
                if password != confirm_password:
                    st.error("✗ 비밀번호가 일치하지 않습니다.")
                elif len(password) < 8:
                    st.error("✗ 비밀번호는 8자 이상이어야 합니다.")
                else:
                    st.success("✓ 비밀번호가 유효합니다.")

            server = st.text_input(
                "서버", placeholder="#095 woLF", key="new_admin_server"
            )
            alliance = st.text_input(
                "연맹", placeholder="선택사항", key="new_admin_alliance"
            )

        with col2:
            st.markdown("### 💡 안내")

            st.markdown("""
            - **사용자명**: 관리자 로그인용 아이디
            - **닉네임**: 표시용 이름 (필수)
            - **비밀번호**: 8자 이상
            - **서버**: 소속 서버 (자유 입력)
            - **연맹**: 소속 연맹 (선택사항)

            **권한**:
            - 예약 승인/거절
            - 참여자 관리
            - 블랙리스트 관리
            - 공지사항 작성

            마스터 계정만 관리자를 생성/삭제할 수 있습니다.
            """)

        # 추가 버튼
        st.markdown("---")
        if st.button("관리자 추가", type="primary", use_container_width=True):
            if not username:
                st.error("사용자명을 입력해주세요.")
                return

            if not nickname:
                st.error("닉네임을 입력해주세요.")
                return

            if not password or not confirm_password:
                st.error("비밀번호를 입력해주세요.")
                return

            if password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
                return

            if len(password) < 8:
                st.error("비밀번호는 8자 이상이어야 합니다.")
                return

            try:
                admin_id = db.create_user(
                    username=username,
                    commander_id=None,
                    password=password,
                    role="admin",
                    nickname=nickname,
                    server=server if server else None,
                    alliance=alliance if alliance else None,
                )

                st.success(f"✓ 관리자가 생성되었습니다! (ID: {admin_id})")
                st.info("생성된 관리자는 바로 로그인할 수 있습니다.")
                st.rerun()

            except Exception as e:
                st.error(f"생성 중 오류가 발생했습니다: {e}")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 마스터 안내

    - **관리자 권한**: 예약/참여자/블랙리스트/공지사항 관리
    - **마스터 권한**: 위 권한 + 관리자 계정 관리
    - **비밀번호**: 최소 8자, 마스터는 초기화 가능

    **보안 팁**:
    - 관리자 비밀번호는 정기적으로 변경하세요
    - 의심스러운 활동은 즉시 조사하세요
    - 불필요한 관리자는 삭제하세요
    """)

    # 현재 마스터 계정 정보 표시
    st.markdown("---")
    st.markdown("### 👑 현재 마스터 계정")

    st.info(f"""
    **사용자명**: {user.get("username", "Unknown")}
    **닉네임**: {user.get("nickname", "Unknown")}
    **로그인 시간**: {st.session_state.get("dice_login_time", "Unknown")}
    """)
