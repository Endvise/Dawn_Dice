#!/usr/bin/env python3
"""
회원가입 페이지
"""

import streamlit as st
import re
import database as db
import auth


# 사령관번호 유효성 검사
def validate_commander_id(commander_id: str) -> tuple[bool, str]:
    """
    사령관번호 유효성을 검사합니다.

    Returns: (유효 여부, 에러 메시지)
    """
    # 공백 제거
    commander_id = commander_id.strip()

    # 빈 값 체크
    if not commander_id:
        return False, "사령관번호를 입력해주세요."

    # 숫자만 허용
    if not commander_id.isdigit():
        return False, "사령관번호는 숫자로만 구성되어야 합니다."

    # 자릿수 체크 (10자리)
    if len(commander_id) != 10:
        return False, "사령관번호는 10자리여야 합니다."

    # 중복 체크
    existing = db.get_user_by_commander_id(commander_id)
    if existing:
        return False, "이미 등록된 사령관번호입니다."

    # 블랙리스트 체크
    blacklisted = db.check_blacklist(commander_id)
    if blacklisted:
        return (
            False,
            f"블랙리스트에 등록된 사령관번호입니다. (사유: {blacklisted.get('reason', 'N/A')})",
        )

    return True, ""


# 비밀번호 유효성 검사
def validate_password(password: str, confirm_password: str) -> tuple[bool, str]:
    """
    비밀번호 유효성을 검사합니다.

    Returns: (유효 여부, 에러 메시지)
    """
    # 길이 체크
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."

    # 일치 여부 체크
    if password != confirm_password:
        return False, "비밀번호가 일치하지 않습니다."

    return True, ""


def show():
    """회원가입 페이지 표시"""
    st.title("🎲 회원가입")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 사용자 등록")
        st.info("사령관번호로 외부인 가입을 받습니다.")

        # 닉네임
        nickname = st.text_input(
            "닉네임", key="reg_nickname", placeholder="닉네임을 입력하세요"
        )

        # 사령관번호
        commander_id = st.text_input(
            "사령관번호", key="reg_commander_id", placeholder="10자리 숫자"
        )

        # 사령관번호 검증 표시
        if commander_id:
            is_valid, error_msg = validate_commander_id(commander_id)

            if is_valid:
                st.success("✓ 유효한 사령관번호입니다.")
            else:
                st.error(f"✗ {error_msg}")

        # 서버 입력
        server = st.text_input(
            "서버", key="reg_server", placeholder="서버명을 입력하세요"
        )

        # 연맹 (선택사항)
        alliance = st.text_input(
            "연맹이름", key="reg_alliance", placeholder="소속 연맹이 있다면 입력하세요"
        )

        # 비밀번호
        password = st.text_input(
            "비밀번호", type="password", key="reg_password", placeholder="8자 이상"
        )
        confirm_password = st.text_input(
            "비밀번호 확인", type="password", key="reg_confirm_password"
        )

        # 비밀번호 검증 표시
        if password and confirm_password:
            is_valid, error_msg = validate_password(password, confirm_password)

            if is_valid:
                st.success("✓ 비밀번호가 유효합니다.")
            else:
                st.error(f"✗ {error_msg}")

        st.markdown("---")

        # 버튼 영역
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

        with col_btn2:
            # 가입 버튼
            if st.button("가입하기", use_container_width=True, type="primary"):
                # 필수 필드 체크
                if not all(
                    [nickname, commander_id, server, password, confirm_password]
                ):
                    st.error("모든 필수 항목을 입력해주세요.")
                    return

                # 사령관번호 검증
                is_valid_id, error_id = validate_commander_id(commander_id)
                if not is_valid_id:
                    st.error(error_id)
                    return

                # 비밀번호 검증
                is_valid_pwd, error_pwd = validate_password(password, confirm_password)
                if not is_valid_pwd:
                    st.error(error_pwd)
                    return

                # 사용자 생성
                try:
                    user_id = db.create_user(
                        username=None,
                        commander_id=commander_id,
                        password=password,
                        role="user",
                        nickname=nickname,
                        server=server,
                        alliance=alliance if alliance else None,
                    )

                    st.success(f"✓ 회원가입이 완료되었습니다! (ID: {user_id})")
                    st.info("이제 로그인 페이지에서 로그인하세요.")

                    # 로그인 페이지로 이동
                    if st.button("로그인 페이지로 이동", use_container_width=True):
                        st.session_state["show_register"] = False
                        st.rerun()

                except Exception as e:
                    st.error(f"가입 중 오류가 발생했습니다: {e}")

            # 취소 버튼
            if st.button("취소", use_container_width=True):
                st.session_state["show_register"] = False
                st.rerun()

        # 안내 메시지
        st.markdown("---")
        st.markdown("""
        ### 💡 가입 안내

        - **사령관번호**: 10자리 숫자여야 합니다.
        - **비밀번호**: 최소 8자 이상이어야 합니다.
        - **연맹**: 선택사항입니다.
        - 이미 블랙리스트에 등록된 사령관번호는 가입할 수 없습니다.
        """)
