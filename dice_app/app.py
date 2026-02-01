#!/usr/bin/env python3
"""
주사위 예약 시스템 메인 애플리케이션
"""

import streamlit as st
import auth
import database as db
import security_utils


def main():
    """메인 애플리케이션"""
    # 페이지 설정
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
    security_utils.inject_devtools_block()

    # 사이드바
    with st.sidebar:
        st.title("🎲 DaWn Dice Party")
        st.markdown("by 엔티티")
        st.markdown("---")

        # 페이지 선택 (로그인 상태에 따라)
        if auth.is_authenticated():
            st.markdown("### 📋 메뉴")

            # 일반 사용자/관리자/마스터 공통 메뉴
            page = st.radio("페이지 선택", ["🏠 홈", "📝 예약 신청", "📊 내 예약 현황"])

            # 관리자/마스터 메뉴 (관리자 페이지 변수 초기화)
            admin_page = None
            if auth.is_admin():
                st.markdown("---")
                st.markdown("### 🔧 관리자 메뉴")

                admin_page = st.radio(
                    "관리자 페이지",
                    [
                        "📊 대시보드",
                        "🎲 회차 관리",
                        "📋 예약 관리",
                        "👥 참여자 관리",
                        "🚫 블랙리스트 관리",
                        "📢 공지사항 관리",
                    ],
                )

            # 마스터 전용 메뉴
            if auth.is_master():
                st.markdown("---")
                st.markdown("### 👑 마스터 메뉴")
                if st.button("👤 관리자 계정 관리"):
                    st.session_state["page"] = "admin_management"
                    st.rerun()

            # 사용자 정보
            auth.show_user_info()
        else:
            st.markdown("### 📋 메뉴")
            page = "로그인"

    # 메인 컨텐츠 영역
    if auth.is_authenticated():
        # 일반 사용자/관리자/마스터 공통 페이지
        if page == "🏠 홈":
            import views.home

            views.home.show()
        elif page == "📝 예약 신청":
            import views.reservation

            views.reservation.show()
        elif page == "📊 내 예약 현황":
            import views.my_reservations

            views.my_reservations.show()

        # 관리자/마스터 전용 페이지
        if auth.is_admin():
            if admin_page == "📊 대시보드":
                import views.admin_dashboard

                views.admin_dashboard.show()
            elif admin_page == "🎲 회차 관리":
                import views.event_sessions

                views.event_sessions.show()
            elif admin_page == "📋 예약 관리":
                import views.admin_reservations

                views.admin_reservations.show()
            elif admin_page == "👥 참여자 관리":
                import views.admin_participants

                views.admin_participants.show()
            elif admin_page == "🚫 블랙리스트 관리":
                import views.admin_blacklist

                views.admin_blacklist.show()
            elif admin_page == "📢 공지사항 관리":
                import views.admin_announcements

                views.admin_announcements.show()

        # 마스터 전용 페이지
        if auth.is_master():
            if st.session_state.get("page") == "admin_management":
                import views.master_admin

                views.master_admin.show()

    else:
        # 로그인 전 처리
        if st.session_state.get("show_register"):
            import views.register

            views.register.show()
        else:
            # 홈페이지
            import views.home

            views.home.show()


if __name__ == "__main__":
    main()
