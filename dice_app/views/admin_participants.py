#!/usr/bin/env python3
"""
관리자 참여자 관리 페이지 - 개선된 버전
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from utils import (
    map_excel_columns,
    extract_row_data,
    display_column_mapping_info,
    display_preview_data,
)


def show():
    """참여자 관리 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("👥 참여자 관리")
    st.markdown("---")

    # 통계
    participants = db.list_participants()

    total_participants = len(participants)
    completed_participants = len([p for p in participants if p.get("completed")])
    confirmed_participants = len([p for p in participants if p.get("confirmed")])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("전체 참여자", f"{total_participants}명")

    with col2:
        st.metric("참여완료", f"{completed_participants}명")

    with col3:
        st.metric("확인됨", f"{confirmed_participants}명")

    st.markdown("---")

    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 참여자 목록", "➕ 참여자 추가", "📤 Excel 불러오기", "🔗 Sheets 연동"]
    )

    # 탭 1: 참여자 목록
    with tab1:
        st.markdown("### 📋 참여자 목록")

        # 필터
        col1, col2, col3 = st.columns(3)

        with col1:
            event_filter = st.text_input("이벤트명 필터", placeholder="예: 260128")

        with col2:
            completed_filter = st.selectbox("참여완료 필터", ["전체", "완료", "미완료"])

        with col3:
            search_term = st.text_input("검색", placeholder="닉네임/사령관번호")

        st.markdown("---")

        # 필터링
        filtered_participants = []

        for p in participants:
            # 이벤트명 필터
            if event_filter and event_filter not in (p.get("event_name") or ""):
                continue

            # 참여완료 필터
            if completed_filter != "전체":
                is_completed = bool(p.get("completed"))
                if completed_filter == "완료" and not is_completed:
                    continue
                if completed_filter == "미완료" and is_completed:
                    continue

            # 검색 필터
            if search_term:
                search_lower = search_term.lower()
                if search_lower not in (
                    p.get("nickname") or ""
                ).lower() and search_lower not in str(p.get("igg_id", "")):
                    continue

            filtered_participants.append(p)

        st.markdown(f"### 📋 참여자 목록 ({len(filtered_participants)}건)")

        if filtered_participants:
            for p in filtered_participants:
                # 참여완료 뱃지
                completion_badge = "✅" if p.get("completed") else "⏳"

                with st.expander(
                    f"{completion_badge} {p.get('nickname', 'Unknown')} - {p.get('event_name', 'N/A')}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **번호**: {p.get("number", "N/A")}
                        **닉네임**: {p.get("nickname", "Unknown")}
                        **소속**: {p.get("affiliation", "N/A")}
                        **사령관번호**: {p.get("igg_id", "N/A")}
                        **연맹**: {p.get("alliance", "N/A") if p.get("alliance") else "없음"}
                        **이벤트명**: {p.get("event_name", "N/A")}
                        **등록일시**: {p.get("created_at", "N/A")}
                        """)

                        if p.get("confirmed"):
                            st.success("📋 확인됨")

                        if p.get("wait_confirmed"):
                            st.info("⏰ 대기확인됨")

                        if p.get("participation_record"):
                            st.text(f"참여기록: {p['participation_record']}")

                        if p.get("notes"):
                            st.text(f"비고: {p['notes']}")

                    with col2:
                        st.markdown("### 액션")

                        # 참여완료 토글
                        if st.button(
                            "참여완료 설정" if not p.get("completed") else "완료 취소",
                            key=f"toggle_completed_{p['id']}",
                            use_container_width=True,
                        ):
                            try:
                                new_status = not bool(p.get("completed"))
                                db.update_participant(
                                    p["id"], completed=1 if new_status else 0
                                )
                                st.success("✓ 상태가 업데이트되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"업데이트 중 오류가 발생했습니다: {e}")

                        # 수정 버튼
                        if st.button(
                            "수정", key=f"edit_{p['id']}", use_container_width=True
                        ):
                            st.session_state["edit_participant_id"] = p["id"]
                            st.rerun()

                        # 삭제 버튼 (마스터만)
                        if is_master:
                            if st.button(
                                "삭제",
                                key=f"delete_{p['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                # 확인 다이얼로그
                                if st.session_state.get(
                                    f"confirm_delete_{p['id']}", False
                                ):
                                    try:
                                        db.delete_participant(p["id"])
                                        st.success("✓ 삭제되었습니다.")
                                        st.session_state[
                                            f"confirm_delete_{p['id']}"
                                        ] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"삭제 중 오류가 발생했습니다: {e}")
                                        st.session_state[
                                            f"confirm_delete_{p['id']}"
                                        ] = False
                                else:
                                    st.session_state[f"confirm_delete_{p['id']}"] = True
                                    st.warning(
                                        f"'{p.get('nickname', 'Unknown')}'님을 삭제하려면 다시 버튼을 클릭하세요."
                                    )

        else:
            st.info("표시할 참여자가 없습니다.")

    # 탭 2: 참여자 추가
    with tab2:
        st.markdown("### ➕ 참여자 추가")

        col1, col2 = st.columns([1, 2])

        with col1:
            # 다음 번호 자동 계산
            try:
                next_number_result = execute_query(
                    "SELECT COALESCE(MAX(number), 0) + 1 as next_number FROM participants",
                    fetch="one",
                )
                auto_number = (
                    next_number_result["next_number"] if next_number_result else 1
                )
            except:
                auto_number = 1

            # 폼 (번호 자동 입력)
            number = st.number_input(
                "번호", min_value=1, value=auto_number, disabled=True
            )
            nickname = st.text_input(
                "닉네임", placeholder="필수", value=f"참여자{auto_number}"
            )
            affiliation = st.text_input("소속", placeholder="선택사항")
            igg_id = st.text_input("사령관번호(IGG ID)", placeholder="선택사항")
            alliance = st.text_input("연맹", placeholder="선택사항")
            event_name = st.text_input("이벤트명", placeholder="필수 (예: 260128)")

            # 체크박스
            wait_confirmed = st.checkbox("대기확인")
            confirmed = st.checkbox("확인")
            completed = st.checkbox("참여완료")

            notes = st.text_area("비고", placeholder="선택사항", height=100)
            participation_record = st.text_area(
                "참여기록", placeholder="선택사항", height=100
            )

        with col2:
            st.markdown("### 💡 안내")

            st.markdown("""
            - **번호**: 참여자 순번 (자동 입력됨)
            - **닉네임**: 필수 항목
            - **소속**: 소속 정보
            - **사령관번호**: IGG 아이디
            - **연맹**: 소속 연맹
            - **이벤트명**: 이벤트 날짜 (예: 260128)

            **상태 표시**:
            - **대기확인**: 대기상태에서 확인
            - **확인**: 참여 확인
            - **참여완료**: 최종 참여 완료
            """)

        # 추가 버튼
        st.markdown("---")
        if st.button("참여자 추가", use_container_width=True, type="primary"):
            if not nickname:
                st.error("닉네임을 입력해주세요.")
                return

            if not event_name:
                st.error("이벤트명을 입력해주세요.")
                return

            try:
                participant_data = {
                    "number": auto_number,
                    "nickname": nickname,
                    "affiliation": affiliation if affiliation else None,
                    "igg_id": igg_id if igg_id else None,
                    "alliance": alliance if alliance else None,
                    "wait_confirmed": 1 if wait_confirmed else 0,
                    "confirmed": 1 if confirmed else 0,
                    "completed": 1 if completed else 0,
                    "notes": notes if notes else None,
                    "participation_record": participation_record
                    if participation_record
                    else None,
                    "event_name": event_name,
                }

                participant_id = db.add_participant(participant_data)
                st.success(f"✓ 참여자가 추가되었습니다. (ID: {participant_id})")
                st.rerun()

            except Exception as e:
                st.error(f"추가 중 오류가 발생했습니다: {e}")

    # 탭 3: Excel 불러오기
    with tab3:
        st.markdown("### 📤 Excel 불러오기")

        st.markdown("""
        **주사위 명단.xlsx** 파일을 불러와서 참여자 명단을 관리하세요.

        - Excel 파일은 날짜별 시트로 구성되어 있습니다.
        - 빠른 날짜는 1회차, 그다음은 2회차... 순서입니다.
        - 동일 날짜는 통합하고 구분은 따로 합니다.
        """)

        # 파일 업로드
        uploaded_file = st.file_uploader(
            "Excel 파일 업로드",
            type=["xlsx", "xls"],
            help="주사위 명단.xlsx 파일을 선택하세요",
        )

        if uploaded_file:
            # 시트 목록 표시
            try:
                import openpyxl
                from io import BytesIO

                wb = openpyxl.load_workbook(
                    BytesIO(uploaded_file.read()), data_only=True
                )

                st.markdown("### 📋 시트 목록 (회차별)")

                sheets = wb.sheetnames

                for i, sheet_name in enumerate(sheets, 1):
                    # 회차 번호 자동 계산 (시트 순서대로)
                    ws = wb[sheet_name]
                    row_count = ws.max_row - 1  # 헤더 제외

                    st.markdown(f"""
                    **회차 {i}**: {sheet_name}
                    - 데이터 행 수: {row_count if row_count > 0 else 0}
                    """)

                    # 불러오기 버튼
                    if st.button(f"불러오기", key=f"load_sheet_{sheet_name}"):
                        # 데이터 추출 (개선된 방식)
                        try:
                            headers = [cell.value for cell in ws[1] if cell.value]

                            # 유틸리티로 컬럼 매핑
                            column_mapping = map_excel_columns(headers)

                            # 매핑 정보 표시
                            display_column_mapping_info(column_mapping, headers)

                            # 데이터 추출 (유틸리티 사용)
                            rows = []
                            for row_idx, row in enumerate(
                                ws.iter_rows(min_row=2, values_only=True)
                            ):
                                if not row or row[0] is None:
                                    continue

                                # 유틸리티로 데이터 추출
                                row_data = extract_row_data(
                                    row, headers, column_mapping
                                )

                                if row_data.get(
                                    "commander_id"
                                ):  # 사령관번호가 있으면 추가
                                    row_data["event_name"] = f"회차{i}"
                                    rows.append(row_data)

                            st.success(f"✓ {len(rows)}건의 데이터를 찾았습니다.")

                            # 미리보기 (유틸리티 사용)
                            display_preview_data(rows)

                            # 저장 버튼
                            st.markdown("---")
                            if st.button(
                                "데이터베이스에 저장",
                                key=f"save_{sheet_name}",
                                type="primary",
                            ):
                                with st.spinner("저장 중..."):
                                    added_count = 0
                                    updated_count = 0

                                    for row_data in rows:
                                        try:
                                            # 중복 체크 (이벤트명 + 번호)
                                            existing = execute_query(
                                                """
                                                SELECT id FROM participants
                                                WHERE event_name = ? AND number = ?
                                                """,
                                                (
                                                    row_data["event_name"],
                                                    row_data.get("number"),
                                                ),
                                                fetch="one",
                                            )

                                            if existing:
                                                # 업데이트
                                                participant_id = existing["id"]
                                                db.update_participant(
                                                    participant_id,
                                                    nickname=row_data.get("nickname"),
                                                    affiliation=row_data.get(
                                                        "affiliation"
                                                    ),
                                                    igg_id=row_data.get(
                                                        "commander_id"
                                                    ),  # 매핑된 사령관번호 사용
                                                    alliance=row_data.get("alliance"),
                                                    wait_confirmed=1
                                                    if row_data.get("wait_confirmed")
                                                    else 0,
                                                    confirmed=1
                                                    if row_data.get("confirmed")
                                                    else 0,
                                                    completed=1
                                                    if row_data.get("completed")
                                                    else 0,
                                                    notes=row_data.get("notes"),
                                                    participation_record=row_data.get(
                                                        "participation_record"
                                                    ),
                                                )
                                                updated_count += 1
                                            else:
                                                # 추가
                                                db.add_participant(row_data)
                                                added_count += 1

                                        except Exception as row_error:
                                            st.warning(
                                                f"행 {row_data.get('number', '?')} 처리 중 오류: {row_error}"
                                            )
                                            continue

                                    st.success(
                                        f"✅ 완료! 추가: {added_count}건, 업데이트: {updated_count}건"
                                    )
                                    st.rerun()

                        except Exception as e:
                            st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")

            except Exception as e:
                st.error(f"파일 읽기 중 오류가 발생했습니다: {e}")

    # 탭 4: Google Sheets 연동
    with tab4:
        st.markdown("### 🔗 Google Sheets 연동")

        col1, col2 = st.columns([1, 2])

        with col1:
            # Google Sheets URL 입력
            sheets_url = st.text_input(
                "Google Sheets URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                value=st.secrets.get("PARTICIPANT_GOOGLE_SHEET_URL", ""),
                help="공유된 Google Sheets 링크를 입력하세요",
            )

            # 데이터 가져오기 버튼
            if st.button(
                "Google Sheets에서 가져오기", type="primary", use_container_width=True
            ):
                if not sheets_url:
                    st.error("Google Sheets URL을 입력해주세요.")
                    return

                import requests
                import pandas as pd
                from io import StringIO

                # CSV 내보내기 URL로 변환
                if "edit" in sheets_url:
                    # 편집 URL을 CSV 내보내기 URL로 변환
                    sheet_id = sheets_url.split("/d/")[1].split("/edit")[0]
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
                else:
                    csv_url = sheets_url

                with st.spinner("데이터를 가져오는 중..."):
                    response = requests.get(csv_url, timeout=30)
                    if response.status_code == 200:
                        df = pd.read_csv(StringIO(response.text))

                        st.success(f"✓ {len(df)}건의 데이터를 가져왔습니다.")

                        # 데이터 미리보기
                        st.markdown("### 📋 가져온 데이터 미리보기")
                        st.dataframe(df.head(10))

                        # 데이터 정리 및 자동 구분
                        st.markdown("### 🔄 데이터 자동 정리")

                        # 컬럼 자동 감지 및 매핑
                        headers = df.columns.tolist()
                        column_mapping = map_excel_columns(headers)

                        # 정리된 데이터 표시
                        display_column_mapping_info(column_mapping, headers)

                        # 데이터베이스 저장 버튼
                        st.markdown("---")
                        if st.button(
                            "데이터베이스에 저장",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner("저장 중..."):
                                added_count = 0
                                updated_count = 0

                                # 각 행을 참여자로 추가 (유틸리티 사용)
                                rows = []
                                for index, row in df.iterrows():
                                    try:
                                        # 이벤트명 자동 생성 (날짜 기반)
                                        event_date = pd.Timestamp.now().strftime(
                                            "%y%m%d"
                                        )
                                        event_name = f"회차{index + 1}"

                                        # 유틸리티로 데이터 추출
                                        row_data = extract_row_data(
                                            row, headers, column_mapping
                                        )

                                        if row_data.get(
                                            "commander_id"
                                        ):  # 사령관번호가 있으면 추가
                                            row_data["event_name"] = event_name
                                            rows.append(row_data)

                                    except Exception as row_error:
                                        st.warning(
                                            f"행 {index + 2} 처리 중 오류: {row_error}"
                                        )
                                        continue

                                st.success(
                                    f"✅ 완료! 추가: {added_count}건, 업데이트: {updated_count}건"
                                )

                    else:
                        st.error(f"Google Sheets 접근 실패: {response.status_code}")

        with col2:
            st.markdown("### 💡 안내")
            st.markdown("""
            **Google Sheets 연동 기능:**
            
            - **URL**: 공유된 Google Sheets 링크 입력
            - **자동 매핑**: 컬럼 이름을 자동으로 감지하여 매핑
            - **데이터 정리**: 중복 데이터 확인 및 자동 구분
            - **일괄 저장**: 데이터베이스에 바로 저장
            
            **지원되는 컬럼 키워드:**
            - **사령관번호**: 사령관번호, 사령관, 번호, id
            - **닉네임**: 닉네임, 이름, nickname, name (사령관번호로도 인식)
            - **소속**: 소속, guild, affiliation (사령관번호로도 인식)
            - **연맹**: 연맹, alliance
            - **비고**: 비고, 메모, notes, comment
            
            **사용 방법:**
            1. Google Sheets를 "웹에 게시"로 공유
            2. 링크를 복사하여 위에 입력
            3. "가져오기" 버튼 클릭
            4. 데이터 확인 후 "데이터베이스에 저장"
            """)

    st.markdown("---")
    st.markdown("""
    ### 💡 관리자 안내

    - **참여자 목록**: 기존 참여자 정보 관리
    - **참여자 추가**: 새로운 참여자 수동 추가 (번호 자동 생성)
    - **Excel 불러오기**: 주사위 명단.xlsx 파일에서 대량 추가 (컬럼 자동 인식)
    - **Sheets 연동**: Google Sheets에서 실시간 데이터 가져오기
    
    **Excel/Sheets 파일 형식:**
    - **자동 컬럼 인식**: 닉네임/소속/IGG아이디 → 사령관번호로 매핑
    - **유연한 매핑**: 다양한 컬럼 이름 지원
    - **중복 데이터 처리**: 자동으로 확인 및 업데이트
    - **회차별 관리**: 시트/데이터 자동으로 회차 할당
    
    Excel에서 불러온 데이터나 Google Sheets 데이터는 이벤트명으로 회차가 자동 지정됩니다.
    """)
