#!/usr/bin/env python3
"""
Excel to Supabase Uploader
엑셀 파일을 읽어서 Supabase에 자동 업로드
"""

import streamlit as st
import pandas as pd
import database as db
from typing import Dict, List, Optional
from datetime import datetime


# 테이블별 컬럼 매핑
TABLE_MAPPINGS = {
    "users": {
        "사령관번호": "commander_id",
        "닉네임": "nickname",
        "서버": "server",
        "연맹": "alliance",
        "비밀번호": "password_hash",
        "username": "username",
        "role": "role",
    },
    "participants": {
        "번호": "number",
        "닉네임": "nickname",
        "소속": "affiliation",
        "IGG ID": "igg_id",
        "연맹": "alliance",
        "이벤트명": "event_name",
        "참여완료": "completed",
        "확인": "confirmed",
        "대기확인": "wait_confirmed",
        "비고": "notes",
    },
    "blacklist": {
        "사령관번호": "commander_id",
        "닉네임": "nickname",
        "사유": "reason",
    },
    "reservations": {
        "닉네임": "nickname",
        "사령관번호": "commander_id",
        "서버": "server",
        "연맹": "alliance",
        "상태": "status",
        "비고": "notes",
    },
}


def normalize_column_names(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Normalize column names to Supabase column names."""
    mapping = TABLE_MAPPINGS.get(table_name, {})
    rename_dict = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        for key, value in mapping.items():
            if key.lower() == col_lower or col_lower == key.lower().replace(" ", "_"):
                rename_dict[col] = value
                break
    return df.rename(columns=rename_dict)


def validate_data(df: pd.DataFrame, table_name: str) -> tuple[bool, List[str]]:
    """Validate data before upload."""
    errors = []
    required_fields = {
        "users": ["commander_id", "password_hash"],
        "blacklist": ["commander_id"],
        "reservations": ["commander_id", "nickname"],
    }
    required = required_fields.get(table_name, [])
    for field in required:
        if field not in df.columns:
            errors.append(f"필수 컬럼 '{field}'이(가) 없습니다.")
    return len(errors) == 0, errors


def upload_excel_to_supabase(
    uploaded_file,
    table_name: str,
    skip_rows: int = 0,
) -> Dict:
    """Upload Excel file to Supabase."""
    try:
        # 엑셀/CSV 파일 읽기
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, skiprows=skip_rows)
        else:
            df = pd.read_excel(uploaded_file, skiprows=skip_rows)

        st.write(f"**읽은 데이터:** {len(df)}행")
        with st.expander("데이터 미리보기"):
            st.dataframe(df.head(10))

        # 컬럼명 정규화
        df = normalize_column_names(df, table_name)
        st.write(f"**정규화된 컬럼:** {list(df.columns)}")

        # 데이터 검증
        is_valid, errors = validate_data(df, table_name)
        if not is_valid:
            return {"success": False, "errors": errors}

        # Supabase에 업로드
        records = df.to_dict("records")
        uploaded_count = 0
        failed_count = 0
        error_messages = []

        progress_bar = st.progress(0)
        for i, record in enumerate(records):
            result = db.insert(table_name, record)
            progress_bar.progress((i + 1) / len(records))

            if result:
                uploaded_count += 1
            else:
                failed_count += 1
                error_messages.append(f"행 {i + 1}: INSERT 실패")

        progress_bar.empty()

        return {
            "success": failed_count == 0,
            "uploaded": uploaded_count,
            "failed": failed_count,
            "total": len(records),
            "errors": error_messages,
        }

    except Exception as e:
        return {"success": False, "errors": [f"업로드 오류: {str(e)}"]}


def show_excel_upload_page():
    """Excel Upload Admin Page."""
    st.title("📤 Excel → Supabase 업로드")

    st.info("""
    **사용 방법:**
    1. 업로드할 테이블 선택
    2. 엑셀/CSV 파일 선택
    3. 데이터 미리보기 확인
    4. Supabase에 업로드
    """)

    st.markdown("---")

    # 테이블 선택
    table = st.selectbox(
        "업로드할 테이블 선택",
        ["users", "participants", "blacklist", "reservations"],
        format_func=lambda x: {
            "users": "👤 사용자",
            "participants": "📋 참여자",
            "blacklist": "🚫 블랙리스트",
            "reservations": "📅 예약",
        }[x],
    )

    # 테이블별 필수 컬럼 안내
    table_info = {
        "users": "필수: 사령관번호, 비밀번호",
        "participants": "필수: 닉네임",
        "blacklist": "필수: 사령관번호",
        "reservations": "필수: 사령관번호, 닉네임",
    }
    st.caption(f"📌 {table_info[table]}")

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "엑셀/CSV 파일 선택",
        type=["xlsx", "csv"],
        help="첫 번째 행이 컬럼명으로 사용됩니다.",
    )

    if uploaded_file:
        # 미리보기
        if st.checkbox("데이터 미리보기", value=True):
            try:
                if uploaded_file.name.endswith(".csv"):
                    preview_df = pd.read_csv(uploaded_file)
                else:
                    preview_df = pd.read_excel(uploaded_file)
                st.dataframe(preview_df.head(5))
                st.caption(f"총 {len(preview_df)}행")
            except Exception as e:
                st.error(f"미리보기 오류: {e}")

        # 업로드 옵션
        with st.expander("고급 옵션"):
            skip_rows = st.number_input("건너뛸 행 수", min_value=0, value=0)

        # 업로드 버튼
        st.markdown("---")
        if st.button("🚀 Supabase에 업로드", type="primary", use_container_width=True):
            with st.spinner("업로드 중..."):
                result = upload_excel_to_supabase(
                    uploaded_file,
                    table,
                    skip_rows=skip_rows,
                )

            if result["success"]:
                st.success(
                    f"✅ 업로드 완료! "
                    f"성공: {result['uploaded']}행"
                    + (
                        f", 실패: {result['failed']}행"
                        if result.get("failed", 0) > 0
                        else ""
                    )
                )
            else:
                st.error("❌ 업로드 실패:")
                for error in result.get("errors", []):
                    st.write(f"- {error}")

            # 오류가 있으면 상세 정보 표시
            if result.get("errors") and len(result["errors"]) > 10:
                st.warning(f"총 {len(result['errors'])}개의 오류가 발생했습니다.")


def show_blacklist_sync_page():
    """Blacklist Synchronization Page."""
    st.title("🔄 블랙리스트 동기화")

    st.info("Google Sheets에서 블랙리스트를 가져와 Supabase에 동기화합니다.")

    # 현재 블랙리스트 수
    current_count = len(db.list_blacklist(is_active=True))
    st.metric("현재 Supabase 블랙리스트", f"{current_count}명")

    # 동기화 버튼
    if st.button("🔄 Google Sheets에서 동기화", type="primary"):
        with st.spinner("동기화 중..."):
            try:
                import requests as req
                import pandas as pd
                from io import StringIO

                sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
                if not sheet_url:
                    st.error("Google Sheets URL이 설정되지 않았습니다.")
                    return

                # Google Sheets에서 데이터 가져오기
                response = req.get(sheet_url)
                if response.status_code != 200:
                    st.error(f"Google Sheets 접근 실패: {response.status_code}")
                    return

                # CSV로 읽기
                try:
                    df = pd.read_csv(StringIO(response.text), on_bad_lines="skip")
                except Exception:
                    df = pd.read_csv(
                        StringIO(response.text),
                        on_bad_lines="skip",
                        encoding="utf-8-sig",
                    )

                # 사령관번호 컬럼 찾기
                commander_col = None
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in [
                        "commander_number",
                        "commander_id",
                        "사령관번호",
                        "igg_id",
                    ]:
                        commander_col = col
                        break

                if not commander_col:
                    st.error("사령관번호 컬럼을 찾을 수 없습니다.")
                    return

                sheet_count = len(df)
                st.write(f"Google Sheets에서 **{sheet_count}**개의 항목을 찾았습니다.")

                # 기존 블랙리스트와 비교
                existing = db.list_blacklist(is_active=True)
                existing_ids = {item["commander_number"] for item in existing}

                # 새 항목 업로드
                new_count = 0
                skip_count = 0
                for _, row in df.iterrows():
                    commander_id = str(row[commander_col]).strip()
                    if not commander_id:
                        skip_count += 1
                        continue

                    if commander_id in existing_ids:
                        skip_count += 1
                        continue

                    db.add_to_blacklist(
                        commander_number=commander_id,
                        nickname=str(row.get("nickname", "")).strip() or None,
                        reason=f"Google Sheets 동기화 - {datetime.now().strftime('%Y-%m-%d')}",
                    )
                    new_count += 1

                st.success(
                    f"✅ 동기화 완료!\n\n- 새 항목 추가: {new_count}개\n- 기존 항목 스킵: {skip_count}개\n- 총 블랙리스트: {current_count + new_count}개"
                )

            except Exception as e:
                st.error(f"동기화 실패: {str(e)}")


if __name__ == "__main__":
    tab1, tab2 = st.tabs(["📤 Excel 업로드", "🔄 블랙리스트 동기화"])
    with tab1:
        show_excel_upload_page()
    with tab2:
        show_blacklist_sync_page()
