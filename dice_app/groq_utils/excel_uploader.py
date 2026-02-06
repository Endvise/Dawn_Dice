#!/usr/bin/env python3
"""
Excel to Supabase Uploader
Reads Excel files and uploads to Supabase automatically
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
            errors.append(f"Required column '{field}' is missing.")
    return len(errors) == 0, errors


def upload_excel_to_supabase(
    uploaded_file,
    table_name: str,
    skip_rows: int = 0,
) -> Dict:
    """Upload Excel file to Supabase."""
    try:
        # Read Excel/CSV file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, skiprows=skip_rows)
        else:
            df = pd.read_excel(uploaded_file, skiprows=skip_rows)

        st.write(f"**Data loaded:** {len(df)} rows")
        with st.expander("Data Preview"):
            st.dataframe(df.head(10))

        # Normalize column names
        df = normalize_column_names(df, table_name)
        st.write(f"**Normalized columns:** {list(df.columns)}")

        # Validate data
        is_valid, errors = validate_data(df, table_name)
        if not is_valid:
            return {"success": False, "errors": errors}

        # Upload to Supabase
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
                error_messages.append(f"Row {i + 1}: INSERT failed")

        progress_bar.empty()

        return {
            "success": failed_count == 0,
            "uploaded": uploaded_count,
            "failed": failed_count,
            "total": len(records),
            "errors": error_messages,
        }

    except Exception as e:
        return {"success": False, "errors": [f"Upload error: {str(e)}"]}


def show_excel_upload_page():
    """Excel Upload Admin Page."""
    st.title("📤 Excel → Supabase Upload")

    st.info("""
    **Usage:**
    1. Select table to upload
    2. Choose Excel/CSV file
    3. Preview data
    4. Upload to Supabase
    """)

    st.markdown("---")

    # Select table
    table = st.selectbox(
        "Select table to upload",
        ["users", "participants", "blacklist", "reservations"],
        format_func=lambda x: {
            "users": "👤 Users",
            "participants": "📋 Participants",
            "blacklist": "🚫 Blacklist",
            "reservations": "📅 Reservations",
        }[x],
    )

    # Required columns per table
    table_info = {
        "users": "Required: commander_id, password",
        "participants": "Required: nickname",
        "blacklist": "Required: commander_id",
        "reservations": "Required: commander_id, nickname",
    }
    st.caption(f"📌 {table_info[table]}")

    # File upload
    uploaded_file = st.file_uploader(
        "Select Excel/CSV file",
        type=["xlsx", "csv"],
        help="First row will be used as column names.",
    )

    if uploaded_file:
        # Preview
        if st.checkbox("Data Preview", value=True):
            try:
                if uploaded_file.name.endswith(".csv"):
                    preview_df = pd.read_csv(uploaded_file)
                else:
                    preview_df = pd.read_excel(uploaded_file)
                st.dataframe(preview_df.head(5))
                st.caption(f"Total: {len(preview_df)} rows")
            except Exception as e:
                st.error(f"Preview error: {e}")

        # Upload options
        with st.expander("Advanced Options"):
            skip_rows = st.number_input("Rows to skip", min_value=0, value=0)

        # Upload button
        st.markdown("---")
        if st.button("🚀 Upload to Supabase", type="primary", use_container_width=True):
            with st.spinner("Uploading..."):
                result = upload_excel_to_supabase(
                    uploaded_file,
                    table,
                    skip_rows=skip_rows,
                )

            if result["success"]:
                st.success(
                    f"✅ Upload complete! "
                    f"Success: {result['uploaded']} rows"
                    + (
                        f", Failed: {result['failed']} rows"
                        if result.get("failed", 0) > 0
                        else ""
                    )
                )
            else:
                st.error("❌ Upload failed:")
                for error in result.get("errors", []):
                    st.write(f"- {error}")

            # Show error details
            if result.get("errors") and len(result["errors"]) > 10:
                st.warning(f"Total {len(result['errors'])} errors occurred.")


def show_blacklist_sync_page():
    """Blacklist Synchronization Page."""
    st.title("🔄 Blacklist Sync")

    st.info("Fetch blacklist from Google Sheets and sync to Supabase.")

    # Current blacklist count
    current_count = len(db.list_blacklist(is_active=True))
    st.metric("Current Supabase Blacklist", f"{current_count}")

    # Sync button
    if st.button("🔄 Sync from Google Sheets", type="primary"):
        with st.spinner("Syncing..."):
            try:
                import requests as req
                import pandas as pd
                from io import StringIO

                sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
                if not sheet_url:
                    st.error("Google Sheets URL not configured.")
                    return

                # Fetch data from Google Sheets
                response = req.get(sheet_url)
                if response.status_code != 200:
                    st.error(f"Google Sheets access failed: {response.status_code}")
                    return

                # Read as CSV
                try:
                    df = pd.read_csv(StringIO(response.text), on_bad_lines="skip")
                except Exception:
                    df = pd.read_csv(
                        StringIO(response.text),
                        on_bad_lines="skip",
                        encoding="utf-8-sig",
                    )

                # Find commander_number column
                commander_col = None
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in [
                        "commander_number",
                        "commander_id",
                        "igg_id",
                    ]:
                        commander_col = col
                        break

                if not commander_col:
                    st.error("Cannot find commander_number column.")
                    return

                sheet_count = len(df)
                st.write(f"Found **{sheet_count}** items from Google Sheets.")

                # Compare with existing blacklist
                existing = db.list_blacklist(is_active=True)
                existing_ids = {item["commander_number"] for item in existing}

                # Upload new items
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
                        reason=f"Google Sheets sync - {datetime.now().strftime('%Y-%m-%d')}",
                    )
                    new_count += 1

                st.success(
                    f"✅ Sync complete!\n\n- New items added: {new_count}\n- Skipped existing: {skip_count}\n- Total blacklist: {current_count + new_count}"
                )

            except Exception as e:
                st.error(f"Sync failed: {str(e)}")


if __name__ == "__main__":
    tab1, tab2 = st.tabs(["📤 Excel Upload", "🔄 Blacklist Sync"])
    with tab1:
        show_excel_upload_page()
    with tab2:
        show_blacklist_sync_page()
