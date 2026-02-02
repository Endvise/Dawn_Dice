#!/usr/bin/env python3
"""
엑셀 처리 유틸리티 모듈
"""


def map_excel_columns(headers):
    """
    엑셀 컬럼을 사령관번호 중심으로 자동 매핑
    - 닉네임/소속/IGG아이디 컬럼을 사령관번호로 인식
    """
    mapping = {}

    for idx, header in enumerate(headers):
        header_str = str(header).lower().strip()

        # 사령관번호 관련 컬럼 (우선순위 높음)
        if any(
            keyword in header_str
            for keyword in [
                "사령관번호",
                "사령관",
                "번호",
                "id",
                "igg아이디",
                "igg id",
                "commander",
            ]
        ):
            mapping["commander_id"] = idx

            # 여기서 닉네임/소속을 사령관번호로 사용
            if any(
                keyword in header_str
                for keyword in ["닉네임", "이름", "nickname", "name"]
            ):
                mapping["nickname"] = idx
            elif any(
                keyword in header_str for keyword in ["소속", "guild", "affiliation"]
            ):
                mapping["affiliation"] = idx

        # 일반 컬럼 매핑
        elif any(
            keyword in header_str for keyword in ["닉네임", "이름", "nickname", "name"]
        ):
            mapping["nickname"] = idx
        elif any(keyword in header_str for keyword in ["소속", "guild", "affiliation"]):
            mapping["affiliation"] = idx
        elif any(keyword in header_str for keyword in ["연맹", "alliance"]):
            mapping["alliance"] = idx
        elif any(
            keyword in header_str for keyword in ["비고", "메모", "notes", "comment"]
        ):
            mapping["notes"] = idx
        elif any(keyword in header_str for keyword in ["대기확인", "wait"]):
            mapping["wait_confirmed"] = idx
        elif any(keyword in header_str for keyword in ["확인", "confirm", "confirmed"]):
            mapping["confirmed"] = idx
        elif any(
            keyword in header_str for keyword in ["참여완료", "completed", "참여"]
        ):
            mapping["completed"] = idx
        elif any(
            keyword in header_str for keyword in ["참여기록", "record", "participation"]
        ):
            mapping["participation_record"] = idx

        # 기본값: 첫 컬럼은 사령관번호
        if idx == 0:
            mapping["commander_id"] = idx

    return mapping


def extract_row_data(row, headers, column_mapping):
    """
    엑셀 행 데이터를 추출하여 매핑
    """
    row_data = {}

    # 매핑된 데이터 추출
    for field, col_idx in column_mapping.items():
        if col_idx < len(row) and row[col_idx] is not None:
            cell_value = str(row[col_idx]).strip() if row[col_idx] is not None else None

            if field == "commander_id":
                # 닉네임/소속/IGG아이디 컬럼을 사령관번호로 사용
                header_name = str(headers[col_idx]).lower()
                if any(
                    keyword in header_name
                    for keyword in ["닉네임", "이름", "nickname", "name"]
                ):
                    row_data["nickname"] = cell_value
                    row_data["commander_id"] = cell_value
                elif any(
                    keyword in header_name
                    for keyword in ["소속", "guild", "affiliation"]
                ):
                    row_data["affiliation"] = cell_value
                    row_data["commander_id"] = cell_value
                else:
                    row_data["commander_id"] = cell_value
            else:
                row_data[field] = cell_value

    return row_data


def display_column_mapping_info(column_mapping, headers):
    """
    컬럼 매핑 정보 표시
    """
    if column_mapping:
        st.markdown("### 🗂️ 감지된 컬럼 매핑")
        for field, idx in column_mapping.items():
            col_name = headers[idx] if idx < len(headers) else "N/A"
            st.markdown(f"- **{field}**: `{col_name}` (컬럼 {idx + 1})")


def display_preview_data(rows):
    """
    미리보기 데이터 표시
    """
    if rows:
        st.markdown("### 📋 미리보기 (처음 5건)")
        for preview_row in rows[:5]:
            commander_id = preview_row.get("commander_id", "N/A")
            nickname = preview_row.get("nickname", "N/A")
            st.text(f"- {nickname}: {commander_id}")

        st.info("💡 닉네임/소속/IGG아이디 컬럼을 사령관번호로 자동 인식했습니다.")
