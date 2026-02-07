#!/usr/bin/env python3
"""
User Guide Page - Korean
일반 사용자용 이용 방법
"""

import streamlit as st
import auth


def show():
    """Show user guide (Korean)"""
    auth.require_login()

    st.title("📖 이용 방법")
    st.markdown("---")

    # 목차 (사이드바 메뉴와 일치)
    st.markdown("""
    ## 목차

    01. [홈페이지](#01-홈페이지-home)
    02. [예약 신청](#02-예약-신청-make-reservation)
    03. [내 예약 현황](#03-내-예약-현황-my-reservations)
    04. [이용 방법](#04-이용-방법)
    05. [How to Use](#05-how-to-use)
    06. [비밀번호 변경](#06-비밀번호-변경-change-password)
    """)

    st.markdown("---")

    # 01. 홈페이지
    st.markdown("## 01. 홈페이지 (Home)")
    st.markdown("""
    **메뉴 위치:** 사이드바 첫 번째

    **기능 설명:**
    - 시스템의 메인 페이지입니다
    - 현재 활성화된 세션 정보를 보여줍니다
    - 예약 현황 (오픈/마감/대기중) 상태를 표시합니다
    - 예약 오픈/마감 시간을 확인할 수 있습니다

    **사용 방법:**
    1. 사이드바에서 "01. 🏠 Home" 선택
    2. 현재 세션 정보 확인
    3. 예약 상태 확인
    """)

    st.markdown("---")

    # 02. 예약 신청
    st.markdown("## 02. 예약 신청 (Make Reservation)")
    st.markdown("""
    **메뉴 위치:** 사이드바 두 번째

    **기능 설명:**
    - 예약을 신청하는 페이지입니다
    - 관리자가 설정한 예약 가능 시간에만 신청 가능합니다

    **사용 방법:**
    1. 사이드바에서 "02. 📝 Make Reservation" 선택
    2. 사령관번호 입력 (10자리)
    3. 닉네임, 서버, 연맹 정보 확인
    4. 예약 제출

    **예약 가능 시간:**
    - 상단의 **Reservations Open** 상태 확인
    - 예약 오픈 시간: 관리자가 설정한 시간
    - 예약 마감 시간: 설정된 시간 또는 정원 초과 시
    """)

    st.markdown("---")

    # 03. 내 예약 현황
    st.markdown("## 03. 내 예약 현황 (My Reservations)")
    st.markdown("""
    **메뉴 위치:** 사이드바 세 번째

    **기능 설명:**
    - 로그인한 사용자의 예약 현황을 보여줍니다
    - 예약 순서와 상태를 확인할 수 있습니다

    **사용 방법:**
    1. 사이드바에서 "03. 📊 My Reservations" 선택
    2. 내 예약 목록 확인
    3. 예약 순서 (Queue Position) 확인
    - 정원 내: "You are #{순서} in queue (within capacity)"
    - 대기자: "You are #{순서} in queue (waitlist #{대기순서})"
    """)

    st.markdown("---")

    # 04. 이용 방법
    st.markdown("## 04. 이용 방법")
    st.markdown("""
    **메뉴 위치:** 사이드바 네 번째

    **기능 설명:**
    - 현재 보고 있는 이 이용 방법 페이지입니다
    - 시스템 사용 방법을 안내합니다

    **참고:**
    - 이 페이지는 한국어로 제공됩니다
    - 영어로 보려면 "05. How to Use" 메뉴를 선택하세요
    """)

    st.markdown("---")

    # 05. How to Use
    st.markdown("## 05. How to Use")
    st.markdown("""
    **메뉴 위치:** 사이드바 다섯 번째

    **기능 설명:**
    - 영어로 된 이용 방법 페이지입니다
    - Same content as "04. 이용 방법" but in English

    **사용 방법:**
    1. 사이드바에서 "05. 📖 How to Use" 선택
    2. 영어로 된 안내 내용 확인
    """)

    st.markdown("---")

    # 06. 비밀번호 변경
    st.markdown("## 06. 비밀번호 변경 (Change Password)")
    st.markdown("""
    **메뉴 위치:** 사이드바 여섯 번째

    **기능 설명:**
    - 비밀번호를 변경합니다

    **사용 방법:**
    1. 사이드바에서 "06. 🔐 Change Password" 선택
    2. 현재 비밀번호 입력
    3. 새 비밀번호 입력 (8자 이상)
    4. 새 비밀번호 다시 입력
    5. **변경** 버튼 클릭

    **비밀번호를 잊으셨나요?**
    - **관리자에게 문의**하여 비밀번호 초기화를 요청하세요
    - 관리자가 초기화 후 새 비밀번호를 알려드립니다
    """)

    st.markdown("---")

    # 유의사항
    st.markdown("## ⚠️ 유의사항")
    st.markdown("""
    ### 선착순 예약제
    - 먼저 신청한 순서대로 예약이 확정됩니다
    - 정원(180명)이 초과되면 자동으로 대기자로 등록됩니다

    ### 블랙리스트
    - 블랙리스트에 등록된 사령관번호는 이용 불가합니다
    - 문의사항은 관리자에게 연락해주세요

    ### 계정 관련
    - 비밀번호 초기화 후 반드시 새 비밀번호로 변경하세요
    - 사령관번호는 변경이 불가능합니다
    """)

    st.markdown("---")
