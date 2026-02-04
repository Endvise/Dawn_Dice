#!/usr/bin/env python3
"""
Public Reservation Status Page
비로그인 사용자도 확인할 수 있는 예약 현황 페이지
"""

import streamlit as st
import database as db
from datetime import datetime


def show_public_status():
    """Display public reservation status."""
    st.set_page_config(
        page_title="예약 현황 - DaWn Dice Party",
        page_icon="🎲",
        layout="centered",
    )

    st.title("🎲 DaWn Dice Party - 예약 현황")

    # 현재 활성화된 세션 정보
    session = db.get_active_session()
    if not session:
        st.info("📅 현재 진행 중인 예약 세션이 없습니다.")
        st.markdown("""
        ---
        **예약 안내**
        - 예약 오픈 시간은 공지사항을 확인해 주세요.
        - 예약 오픈 시 이 페이지에서 즉시 확인 가능합니다.
        """)
        return

    # 세션 정보 표시
    session_name = session.get(
        "session_name", f"제 {session.get('session_number', 1)}회"
    )
    session_date = session.get("session_date", "")

    st.markdown(f"### 📋 {session_name}")
    if session_date:
        st.markdown(f"**일시:** {session_date}")

    st.markdown("---")

    # 예약 가능 여부 확인
    is_open = session.get("is_reservation_open", False)
    open_time = session.get("reservation_open_time", "")
    close_time = session.get("reservation_close_time", "")

    if not is_open:
        st.warning("🔒 **현재 예약이 마감되었습니다.**")
        if open_time:
            st.info(f"📅 **예약 오픈 시간:** {open_time}")
        if close_time:
            st.info(f"⏰ **예약 마감 시간:** {close_time}")
        return

    # 예약 가능한 상태
    st.success("✅ **예약이 가능합니다!**")

    # 통계 정보
    approved_count = db.get_approved_reservation_count(session.get("id", ""))
    max_participants = session.get("max_participants", 180)
    remaining = max_participants - approved_count

    # 진행률 및 상태
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("예약 현황", f"{approved_count} / {max_participants}")

    with col2:
        if remaining > 0:
            st.metric("남은 자리", f"{remaining}명", delta_color="normal")
        else:
            st.metric("남은 자리", "0명", delta="마감", delta_color="inverse")

    with col3:
        waitlist_count = 0  # Waitlist system not available in simplified schema
        st.metric("대기자", f"{waitlist_count}명")

    # 진행률 바
    progress = min(approved_count / max_participants, 1.0)
    st.progress(progress)

    # 상태 메시지
    st.markdown("---")
    if remaining > 0:
        st.info(f"🎉 **예약 가능!** 아직 {remaining}자리가 남아있습니다.")
    else:
        st.error(
            "⚠️ **정원이 초과되었습니다.**\n\n대기 등록만 가능하며, 대기자 순번은 선착순으로 결정됩니다."
        )

    # 예약 방법 안내
    st.markdown("""
    ---
    ### 📝 예약 방법
    
    1. **회원가입** 버튼을 클릭하여 사령관번호로 가입
    2. 로그인 후 **예약 신청** 메뉴에서 예약
    3. 승인 완료 후 참여 확정
    
    ※ 기존 참여자는 우선순위로 예약이 가능합니다.
    """)


if __name__ == "__main__":
    show_public_status()
