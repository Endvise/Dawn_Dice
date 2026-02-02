#!/usr/bin/env python3
"""
Admin Participants Management Page
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
    """Show participants management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Participants Management")
    st.markdown("---")

    # Statistics
    participants = db.list_participants()

    total_participants = len(participants)
    completed_participants = len([p for p in participants if p.get("completed")])
    confirmed_participants = len([p for p in participants if p.get("confirmed")])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total", f"{total_participants}")

    with col2:
        st.metric("Completed", f"{completed_participants}")

    with col3:
        st.metric("Confirmed", f"{confirmed_participants}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Participants List", "Add Participant", "Import Excel", "Sheets Integration"]
    )

    # Tab 1: Participants list
    with tab1:
        st.markdown("### Participants List")

        col1, col2, col3 = st.columns(3)

        with col1:
            event_filter = st.text_input("Event Filter", placeholder="e.g., 260128")

        with col2:
            completed_filter = st.selectbox(
                "Completion Filter",
                ["All", "Completed", "Incomplete"],
                key="participant_completed_filter",
            )

        with col3:
            search_term = st.text_input("Search", placeholder="Nickname/Commander ID")

        st.markdown("---")

        filtered_participants = []

        for p in participants:
            if event_filter and event_filter not in (p.get("event_name") or ""):
                continue

            if completed_filter != "All":
                is_completed = bool(p.get("completed"))
                if completed_filter == "Completed" and not is_completed:
                    continue
                if completed_filter == "Incomplete" and is_completed:
                    continue

            if search_term:
                search_lower = search_term.lower()
                if search_lower not in (
                    p.get("nickname") or ""
                ).lower() and search_lower not in str(p.get("igg_id", "")):
                    continue

            filtered_participants.append(p)

        st.markdown(f"### Participants ({len(filtered_participants)})")

        if filtered_participants:
            for p in filtered_participants:
                completion_badge = "✅" if p.get("completed") else "⏳"

                with st.expander(
                    f"{completion_badge} {p.get('nickname', 'Unknown')} - {p.get('event_name', 'N/A')}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **Number**: {p.get("number", "N/A")}
                        **Nickname**: {p.get("nickname", "Unknown")}
                        **Affiliation**: {p.get("affiliation", "N/A")}
                        **Commander ID**: {p.get("igg_id", "N/A")}
                        **Alliance**: {p.get("alliance", "N/A") if p.get("alliance") else "None"}
                        **Event**: {p.get("event_name", "N/A")}
                        **Created At**: {p.get("created_at", "N/A")}
                        """)

                        if p.get("confirmed"):
                            st.success("Confirmed")

                        if p.get("wait_confirmed"):
                            st.info("Wait Confirmed")

                        if p.get("participation_record"):
                            st.text(
                                f"Participation Record: {p['participation_record']}"
                            )

                        if p.get("notes"):
                            st.text(f"Notes: {p['notes']}")

                    with col2:
                        st.markdown("### Actions")

                        if st.button(
                            "Set Completed"
                            if not p.get("completed")
                            else "Undo Complete",
                            key=f"toggle_completed_{p['id']}",
                            use_container_width=True,
                        ):
                            try:
                                new_status = not bool(p.get("completed"))
                                db.update_participant(
                                    p["id"], completed=1 if new_status else 0
                                )
                                st.success("Status updated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating: {e}")

                        if st.button(
                            "Edit", key=f"edit_{p['id']}", use_container_width=True
                        ):
                            st.session_state["edit_participant_id"] = p["id"]
                            st.rerun()

                        if is_master:
                            if st.button(
                                "Delete",
                                key=f"delete_{p['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                if st.session_state.get(
                                    f"confirm_delete_{p['id']}", False
                                ):
                                    try:
                                        db.delete_participant(p["id"])
                                        st.success("Deleted.")
                                        st.session_state[
                                            f"confirm_delete_{p['id']}"
                                        ] = False
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
                                        st.session_state[
                                            f"confirm_delete_{p['id']}"
                                        ] = False
                                else:
                                    st.session_state[f"confirm_delete_{p['id']}"] = True
                                    st.warning(
                                        f"Click again to delete '{p.get('nickname', 'Unknown')}'"
                                    )

        else:
            st.info("No participants to display.")

    # Tab 2: Add participant
    with tab2:
        st.markdown("### Add Participant")

        col1, col2 = st.columns([1, 2])

        with col1:
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

            number = st.number_input(
                "Number", min_value=1, value=auto_number, disabled=True
            )
            nickname = st.text_input(
                "Nickname", placeholder="Required", value=f"Participant{auto_number}"
            )
            affiliation = st.text_input("Affiliation", placeholder="Optional")
            igg_id = st.text_input("Commander ID (IGG ID)", placeholder="Optional")
            alliance = st.text_input("Alliance", placeholder="Optional")
            event_name = st.text_input(
                "Event Name", placeholder="Required (e.g., 260128)"
            )

            wait_confirmed = st.checkbox("Wait Confirmed")
            confirmed = st.checkbox("Confirmed")
            completed = st.checkbox("Completed")

            notes = st.text_area("Notes", placeholder="Optional", height=100)
            participation_record = st.text_area(
                "Participation Record", placeholder="Optional", height=100
            )

        with col2:
            st.markdown("### Guide")

            st.markdown("""
            - **Number**: Participant number (auto-filled)
            - **Nickname**: Required
            - **Affiliation**: Affiliation info
            - **Commander ID**: IGG ID
            - **Alliance**: Alliance name
            - **Event Name**: Event date (e.g., 260128)

            **Status:**
            - **Wait Confirmed**: Confirmed from waitlist
            - **Confirmed**: Participation confirmed
            - **Completed**: Final participation complete
            """)

        st.markdown("---")
        if st.button("Add Participant", use_container_width=True, type="primary"):
            if not nickname:
                st.error("Enter nickname.")
                return

            if not event_name:
                st.error("Enter event name.")
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
                st.success(f"Participant added! (ID: {participant_id})")
                st.rerun()

            except Exception as e:
                st.error(f"Error adding: {e}")

    # Tab 3: Import Excel
    with tab3:
        st.markdown("### Import Excel")

        st.markdown("""
        Import participants from **Dice List.xlsx**.

        - Excel files have sheets organized by date
        - Earlier dates are Session 1, next is Session 2, etc.
        - Same dates are integrated, differences are separate.
        """)

        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx", "xls"],
            help="Select Dice List.xlsx file",
        )

        if uploaded_file:
            try:
                import openpyxl
                from io import BytesIO

                wb = openpyxl.load_workbook(
                    BytesIO(uploaded_file.read()), data_only=True
                )

                st.markdown("### Sheet List (by Session)")

                sheets = wb.sheetnames

                for i, sheet_name in enumerate(sheets, 1):
                    ws = wb[sheet_name]
                    row_count = ws.max_row - 1

                    st.markdown(f"""
                    **Session {i}**: {sheet_name}
                    - Data rows: {row_count if row_count > 0 else 0}
                    """)

                    if st.button(f"Import", key=f"load_sheet_{sheet_name}"):
                        try:
                            headers = [cell.value for cell in ws[1] if cell.value]
                            column_mapping = map_excel_columns(headers)
                            display_column_mapping_info(column_mapping, headers)

                            rows = []
                            for row_idx, row in enumerate(
                                ws.iter_rows(min_row=2, values_only=True)
                            ):
                                if not row or row[0] is None:
                                    continue

                                row_data = extract_row_data(
                                    row, headers, column_mapping
                                )

                                if row_data.get("commander_id"):
                                    row_data["event_name"] = f"Session{i}"
                                    rows.append(row_data)

                            st.success(f"Found {len(rows)} records.")

                            display_preview_data(rows)

                            st.markdown("---")
                            if st.button(
                                "Save to Database",
                                key=f"save_{sheet_name}",
                                type="primary",
                            ):
                                with st.spinner("Saving..."):
                                    added_count = 0
                                    updated_count = 0

                                    for row_data in rows:
                                        try:
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
                                                participant_id = existing["id"]
                                                db.update_participant(
                                                    participant_id,
                                                    nickname=row_data.get("nickname"),
                                                    affiliation=row_data.get(
                                                        "affiliation"
                                                    ),
                                                    igg_id=row_data.get("commander_id"),
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
                                                db.add_participant(row_data)
                                                added_count += 1

                                        except Exception as row_error:
                                            st.warning(
                                                f"Error processing row {row_data.get('number', '?')}: {row_error}"
                                            )
                                            continue

                                    st.success(
                                        f"Done! Added: {added_count}, Updated: {updated_count}"
                                    )
                                    st.rerun()

                        except Exception as e:
                            st.error(f"Error processing data: {e}")

            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Tab 4: Google Sheets Integration
    with tab4:
        st.markdown("### Google Sheets Integration")

        col1, col2 = st.columns([1, 2])

        with col1:
            sheets_url = st.text_input(
                "Google Sheets URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                value=st.secrets.get("PARTICIPANT_GOOGLE_SHEET_URL", ""),
                help="Enter shared Google Sheets link",
            )

            if st.button(
                "Import from Google Sheets", type="primary", use_container_width=True
            ):
                if not sheets_url:
                    st.error("Enter Google Sheets URL.")
                    return

                import requests
                import pandas as pd
                from io import StringIO

                if "edit" in sheets_url:
                    sheet_id = sheets_url.split("/d/")[1].split("/edit")[0]
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
                else:
                    csv_url = sheets_url

                with st.spinner("Fetching data..."):
                    response = requests.get(csv_url, timeout=30)
                    if response.status_code == 200:
                        df = pd.read_csv(StringIO(response.text))

                        st.success(f"Imported {len(df)} records.")

                        st.markdown("### Data Preview")
                        st.dataframe(df.head(10))

                        st.markdown("### Auto Process Data")

                        headers = df.columns.tolist()
                        column_mapping = map_excel_columns(headers)
                        display_column_mapping_info(column_mapping, headers)

                        st.markdown("---")
                        if st.button(
                            "Save to Database",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner("Saving..."):
                                added_count = 0
                                updated_count = 0

                                rows = []
                                for index, row in df.iterrows():
                                    try:
                                        event_name = f"Session{index + 1}"
                                        row_data = extract_row_data(
                                            row, headers, column_mapping
                                        )

                                        if row_data.get("commander_id"):
                                            row_data["event_name"] = event_name
                                            rows.append(row_data)

                                    except Exception as row_error:
                                        st.warning(
                                            f"Error processing row {index + 2}: {row_error}"
                                        )
                                        continue

                                st.success(
                                    f"Done! Added: {added_count}, Updated: {updated_count}"
                                )

                    else:
                        st.error(f"Google Sheets access failed: {response.status_code}")

        with col2:
            st.markdown("### Guide")
            st.markdown("""
            **Google Sheets Integration:**

            - **URL**: Enter shared Google Sheets link
            - **Auto Mapping**: Automatically detect and map columns
            - **Data Processing**: Check duplicates and auto-organize
            - **Bulk Save**: Save directly to database

            **Supported Column Keywords:**
            - **Commander ID**: commander_id, commander, number, id
            - **Nickname**: nickname, name
            - **Affiliation**: affiliation, guild
            - **Alliance**: alliance
            - **Notes**: notes, comment
            """)

    st.markdown("---")
    st.markdown("""
    ### Admin Guide

    - **Participants List**: Manage existing participant info
    - **Add Participant**: Manually add new participant (number auto-generated)
    - **Import Excel**: Bulk add from Dice List.xlsx (auto column detection)
    - **Sheets Integration**: Import real-time data from Google Sheets

    **Excel/Sheets Format:**
    - Auto column detection: Nickname/Affiliation/IGG ID
    - Flexible mapping: Support various column names
    - Duplicate handling: Auto check and update
    - Session management: Auto assign sessions

    Data from Excel or Google Sheets is automatically assigned to sessions by event name.
    """)
