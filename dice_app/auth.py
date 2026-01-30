#!/usr/bin/env python3
"""
인증 관리 모듈
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import database as db


# 세션 상태 키
SESSION_KEYS = {
    "authenticated": "dice_authenticated",
    "user_id": "dice_user_id",
    "username": "dice_username",
    "role": "dice_role",
    "nickname": "dice_nickname",
    "login_time": "dice_login_time",
}


def init_session_state():
    """세션 상태를 초기화합니다."""
    for key, session_key in SESSION_KEYS.items():
        if session_key not in st.session_state:
            st.session_state[session_key] = None


def login(username: str, password: str) -> tuple[bool, str]:
    """
    로그인을 시도합니다.
    Returns: (성공 여부, 메시지)
    """
    # 사용자 조회
    user = db.get_user_by_username(username)

    if not user:
        # 사령관번호로도 시도
        user = db.get_user_by_commander_id(username)

    if not user:
        return False, "존재하지 않는 사용자입니다."

    # 계정 비활성화 체크
    if not user.get("is_active"):
        return False, "비활성화된 계정입니다."

    # 로그인 실패 횟수 체크
    max_attempts = st.secrets.get("MAX_LOGIN_ATTEMPTS", 5)
    if user.get("failed_attempts", 0) >= max_attempts:
        return False, "로그인 실패 횟수를 초과했습니다. 관리자에게 연락하세요."

    # 비밀번호 검증
    if not db.verify_password(password, user["password_hash"]):
        # 실패 횟수 증가
        db.update_user(user["id"], failed_attempts=user.get("failed_attempts", 0) + 1)
        return (
            False,
            f"비밀번호가 올바르지 않습니다. (남은 횟수: {max_attempts - user.get('failed_attempts', 0) - 1})",
        )

    # 로그인 성공
    db.update_user(user["id"], failed_attempts=0, last_login=datetime.now())

    # 세션 상태 설정
    st.session_state[SESSION_KEYS["authenticated"]] = True
    st.session_state[SESSION_KEYS["user_id"]] = user["id"]
    st.session_state[SESSION_KEYS["username"]] = user.get("username") or user.get(
        "commander_id"
    )
    st.session_state[SESSION_KEYS["role"]] = user["role"]
    st.session_state[SESSION_KEYS["nickname"]] = user.get("nickname", "")
    st.session_state[SESSION_KEYS["login_time"]] = datetime.now()

    return True, "로그인 성공!"


def logout():
    """로그아웃합니다."""
    for key, session_key in SESSION_KEYS.items():
        st.session_state[session_key] = None
    st.rerun()


def is_authenticated() -> bool:
    """인증 여부를 확인합니다."""
    authenticated = st.session_state.get(SESSION_KEYS["authenticated"])
    if not authenticated:
        return False

    # 세션 타임아웃 체크
    login_time = st.session_state.get(SESSION_KEYS["login_time"])
    if login_time:
        timeout_minutes = st.secrets.get("SESSION_TIMEOUT_MINUTES", 60)
        if (datetime.now() - login_time) > timedelta(minutes=timeout_minutes):
            logout()
            return False

    return True


def get_current_user() -> Optional[Dict[str, Any]]:
    """현재 로그인한 사용자 정보를 반환합니다."""
    if not is_authenticated():
        return None

    user_id = st.session_state.get(SESSION_KEYS["user_id"])
    if user_id:
        return db.get_user_by_id(user_id)
    return None


def get_current_user_id() -> Optional[int]:
    """현재 로그인한 사용자 ID를 반환합니다."""
    return st.session_state.get(SESSION_KEYS["user_id"])


def get_current_role() -> Optional[str]:
    """현재 사용자의 역할을 반환합니다."""
    return st.session_state.get(SESSION_KEYS["role"])


def is_master() -> bool:
    """마스터 권한인지 확인합니다."""
    return get_current_role() == "master"


def is_admin() -> bool:
    """관리자 권한 이상인지 확인합니다."""
    role = get_current_role()
    return role in ["master", "admin"]


def is_user() -> bool:
    """일반 사용자인지 확인합니다."""
    return get_current_role() == "user"


def require_auth(required_role: Optional[str] = None) -> bool:
    """
    인증 및 권한 확인
    Returns: 접근 권한 여부
    """
    # 인증 확인
    if not is_authenticated():
        return False

    # 역할 확인
    if required_role:
        current_role = get_current_role()

        if required_role == "master":
            return is_master()
        elif required_role == "admin":
            return is_admin()
        elif required_role == "user":
            return True  # 인증된 모든 사용자 접근 가능

    return True


def show_login_page():
    """로그인 페이지를 표시합니다."""
    st.title("🎲 주사위 예약 시스템")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("로그인")

        login_method = st.radio(
            "로그인 방식", ["사용자 ID/사령관번호", "마스터 계정"], horizontal=True
        )

        username = st.text_input("ID 또는 사령관번호", key="login_username")
        password = st.text_input("비밀번호", type="password", key="login_password")

        if st.button("로그인", use_container_width=True):
            success, message = login(username, password)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.markdown("---")
        st.markdown("### 계정이 없으신가요?")

        if st.button("회원가입", use_container_width=True):
            st.session_state["show_register"] = True
            st.rerun()


def require_login(required_role: Optional[str] = None, redirect_to: str = "login"):
    """
    로그인이 필요한 페이지에 대한 데코레이터
    """
    if not is_authenticated():
        show_login_page()
        st.stop()

    if required_role:
        current_role = get_current_role()

        if required_role == "master" and not is_master():
            st.error("마스터 권한이 필요합니다.")
            st.stop()
        elif required_role == "admin" and not is_admin():
            st.error("관리자 권한이 필요합니다.")
            st.stop()


def show_user_info():
    """사용자 정보를 표시합니다."""
    user = get_current_user()

    if user:
        role_labels = {"master": "👑 마스터", "admin": "🛡️ 관리자", "user": "👤 사용자"}

        role_label = role_labels.get(user["role"], user["role"])

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 사용자 정보")
        st.sidebar.text(
            f"이름: {user.get('nickname', user.get('username', 'Unknown'))}"
        )
        st.sidebar.text(f"역할: {role_label}")

        if st.sidebar.button("로그아웃"):
            logout()


def get_user_statistics() -> Dict[str, Any]:
    """사용자 통계를 반환합니다."""
    # 예약 수
    if is_user():
        my_reservations = db.list_reservations(user_id=get_current_user_id())
        total_reservations = len(my_reservations)
        pending_reservations = len(
            [r for r in my_reservations if r["status"] == "pending"]
        )
    else:
        total_reservations = len(db.list_reservations())
        pending_reservations = len(db.list_reservations(status="pending"))

    return {
        "total_reservations": total_reservations,
        "pending_reservations": pending_reservations,
        "is_blacklisted": False,  # TODO: 사용자 블랙리스트 체크
    }
