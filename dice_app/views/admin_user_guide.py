#!/usr/bin/env python3
"""
Admin User Guide Page - Korean
관리자용 이용 가이드
"""

import streamlit as st
import auth


def show():
    """Show admin user guide"""
    auth.require_login(required_role="admin")

    st.title("📖 사용 가이드")
    st.markdown("---")

    # 목차
    st.markdown("""
    ## 목차
    
    1. [예약 관리](#예약-관리)
    2. [참가자 관리](#참가자-관리)
    3. [블랙리스트](#블랙리스트)
    4. [공지사항](#공지사항)
    5. [비밀번호 초기화](#비밀번호-초기화)
    """)

    st.markdown("---")

    # 1. 예약 관리
    st.markdown("## 1. 예약 관리")
    st.markdown("""
    - **예약 승인/취소**: 예약 목록에서 개별 승인 또는 취소 가능
    - **대기열 관리**: 정원 초과 시 자동으로 대기열로 이동
    - **현황 확인**: 대시보드에서 실시간 예약 현황 확인
    """)

    st.info("💡 팁: 예약 시간 설정을 통해 자동 오픈/마감 가능")

    st.markdown("---")

    # 2. 참가자 관리
    st.markdown("## 2. 참가자 관리")
    st.markdown("""
    ### Excel 대량 등록
    1. **Participants** → **Import Excel** 탭 선택
    2. Excel 파일 업로드
    3. 컬럼 매핑 (사령관번호 필수)
    4. 자동 생성된 비밀번호로 계정 생성

    ### 개별 추가
    1. **Participants** → **Add** 탭 선택
    2. 정보 입력 후 추가

    ### 기존 세션에서 가져오기
    1. **Participants** → **From Previous Session** 탭
    2. 이전 세션 선택 → 선택한 인원 현재 세션에 추가
    """)

    st.markdown("---")

    # 3. 블랙리스트
    st.markdown("## 3. 블랙리스트")
    st.markdown("""
    - **목적**: 부정 행위 등 특정 사령관번호의 이용 제한
    - **추가 방법**: 블랙리스트 관리에서 직접 추가 또는 파일 업로드
    - **자동 확인**: 로그인 시 자동으로 블랙리스트 여부 확인
    """)

    st.markdown("---")

    # 4. 공지사항
    st.markdown("## 4. 공지사항")
    st.markdown("""
    - **작성**: 공지사항 관리에서 새 공지 작성
    - **수정/삭제**: 기존 공지 수정 또는 비활성화
    - **상단 고정**: 중요한 공지는 상단 고정이 가능
    - **카테고리**: Notice, Guide, Event 중 선택
    """)

    st.markdown("---")

    # 5. 비밀번호 초기화
    st.markdown("## 5. 비밀번호 초기화")
    st.markdown("""
    ### 방법
    1. **Participants** → **Users** 탭 이동
    2. 해당 사용자 선택
    3. **Reset Password** 버튼 클릭
    4. 비밀번호가 **12345678**로 초기화됩니다

    ### 사용자에게 알려줄 내용
    ```
    비밀번호가 초기화되었습니다.
    새 비밀번호: 12345678
    로그인 후 반드시 새 비밀번호로 변경해주세요.
    ```

    ### 주의사항
    - 초기화된 비밀번호(12345678)를 사용자에게 직접 알려주세요
    - 사용자는 로그인 후 새 비밀번호로 변경해야 합니다
    """)

    st.markdown("---")
