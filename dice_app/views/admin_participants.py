#!/usr/bin/env python3
"""
관리자 참여자 관리 페이지
"""

import streamlit as st
import database as db
import auth
from database import execute_query


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
    tab1, tab2, tab3 = st.tabs(
        ["📋 참여자 목록", "➕ 참여자 추가", "📤 Excel 불러오기"]
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
                                if st.confirm("정말 이 참여자를 삭제하시겠습니까?"):
                                    try:
                                        db.delete_participant(p["id"])
                                        st.success("✓ 삭제되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"삭제 중 오류가 발생했습니다: {e}")

        else:
            st.info("표시할 참여자가 없습니다.")

    # 탭 2: 참여자 추가
    with tab2:
        st.markdown("### ➕ 참여자 추가")

        col1, col2 = st.columns([1, 2])

        with col1:
            # 폼
            number = st.number_input("번호", min_value=1, value=1)
            nickname = st.text_input("닉네임", placeholder="필수")
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
            - **번호**: 참여자 순번
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
                    "number": number,
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
                        # 데이터 추출
                        rows = []
                        headers = [cell.value for cell in ws[1]]

                        for row in ws.iter_rows(min_row=2, values_only=True):
                            if row[0] is not None:  # 번호가 있는 행만
                                row_data = dict(zip(headers, row))
                                row_data["event_name"] = f"회차{i}"
                                rows.append(row_data)

                        st.success(f"✓ {len(rows)}건의 데이터를 찾았습니다.")

                        # 미리보기 (처음 5개)
                        if rows:
                            st.markdown("### 📋 미리보기 (처음 5건)")
                            for row in rows[:5]:
                                st.text(
                                    f"- {row.get('nickname', 'N/A')}: {row.get('igg_id', 'N/A')}"
                                )

                            # 저장 버튼
                            if st.button(
                                "데이터베이스에 저장",
                                key=f"save_{sheet_name}",
                                type="primary",
                            ):
                                try:
                                    # 중복 체크 (이벤트명 + 번호)
                                    added_count = 0
                                    updated_count = 0

                                    for row_data in rows:
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
                                                affiliation=row_data.get("소속"),
                                                igg_id=row_data.get("IGG아이디"),
                                                alliance=row_data.get("연맹"),
                                                wait_confirmed=1
                                                if row_data.get("대기확인")
                                                else 0,
                                                confirmed=1
                                                if row_data.get("확인")
                                                else 0,
                                                completed=1
                                                if row_data.get("참여완료")
                                                else 0,
                                                notes=row_data.get("비고"),
                                                participation_record=row_data.get(
                                                    "참여기록"
                                                ),
                                            )
                                            updated_count += 1
                                        else:
                                            # 추가
                                            db.add_participant(row_data)
                                            added_count += 1

                                    st.success(
                                        f"✓ 완료! 추가: {added_count}건, 업데이트: {updated_count}건"
                                    )
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"저장 중 오류가 발생했습니다: {e}")

            except Exception as e:
                st.error(f"파일 읽기 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    st.markdown("""
    ### 💡 관리자 안내

    - **참여자 목록**: 기존 참여자 정보 관리
    - **참여자 추가**: 새로운 참여자 수동 추가
    - **Excel 불러오기**: 주사위 명단.xlsx 파일에서 대량 추가

    **Excel 파일 형식**:
    - 날짜별 시트 구분 (회차별)
    - 첫 번째 행: 헤더
    - 이후 행: 데이터

    Excel에서 불러온 데이터는 이벤트명으로 회차가 자동 지정됩니다.
    """)
