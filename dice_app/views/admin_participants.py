#!/usr/bin/env python3
"""
Admin Participants Management Page
"""

import streamlit as st
import pandas as pd
import openpyxl
import database as db
import auth
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
    tab1, tab2, tab3 = st.tabs(
        ["Participants List", "Add Participant", "Import Excel/CSV"]
    )

    # Tab 1: Participants list with editing
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
            # Edit mode check
            edit_id = st.session_state.get("edit_participant_id")

            if edit_id:
                # Show edit form
                participant = db.fetch_one("participants", {"id": f"eq.{edit_id}"})
                if participant:
                    st.markdown("### Edit Participant")
                    col1, col2 = st.columns(2)

                    with col1:
                        number = st.number_input(
                            "Number",
                            min_value=1,
                            value=int(participant.get("number", 1)),
                        )
                        nickname = st.text_input(
                            "Nickname",
                            value=participant.get("nickname", ""),
                        )
                        affiliation = st.text_input(
                            "Affiliation",
                            value=participant.get("affiliation", "") or "",
                        )
                        igg_id = st.text_input(
                            "Commander ID",
                            value=participant.get("igg_id", "") or "",
                        )
                        alliance = st.text_input(
                            "Alliance",
                            value=participant.get("alliance", "") or "",
                        )
                        event_name = st.text_input(
                            "Event Name",
                            value=participant.get("event_name", "") or "",
                        )

                    with col2:
                        wait_confirmed = st.checkbox(
                            "Wait Confirmed",
                            value=bool(participant.get("wait_confirmed")),
                        )
                        confirmed = st.checkbox(
                            "Confirmed",
                            value=bool(participant.get("confirmed")),
                        )
                        completed = st.checkbox(
                            "Completed",
                            value=bool(participant.get("completed")),
                        )
                        notes = st.text_area(
                            "Notes",
                            value=participant.get("notes", "") or "",
                            height=100,
                        )
                        participation_record = st.text_area(
                            "Participation Record",
                            value=participant.get("participation_record", "") or "",
                            height=100,
                        )

                    st.markdown("---")

                    col_btn1, col_btn2, col_btn3 = st.columns(3)

                    with col_btn1:
                        if st.button(
                            "Save Changes", type="primary", use_container_width=True
                        ):
                            try:
                                db.update_participant(
                                    edit_id,
                                    number=number,
                                    nickname=nickname,
                                    affiliation=affiliation if affiliation else None,
                                    igg_id=igg_id if igg_id else None,
                                    alliance=alliance if alliance else None,
                                    event_name=event_name if event_name else None,
                                    wait_confirmed=1 if wait_confirmed else 0,
                                    confirmed=1 if confirmed else 0,
                                    completed=1 if completed else 0,
                                    notes=notes if notes else None,
                                    participation_record=participation_record
                                    if participation_record
                                    else None,
                                )
                                st.success("Updated successfully!")
                                st.session_state["edit_participant_id"] = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                    with col_btn2:
                        if st.button("Cancel", use_container_width=True):
                            st.session_state["edit_participant_id"] = None
                            st.rerun()

                    with col_btn3:
                        if is_master:
                            if st.button(
                                "Delete", type="secondary", use_container_width=True
                            ):
                                try:
                                    db.delete_participant(edit_id)
                                    st.success("Deleted!")
                                    st.session_state["edit_participant_id"] = None
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                    st.markdown("---")

            # Display participants list
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
            # Get next number
            all_participants = db.list_participants()
            max_number = max([p.get("number", 0) for p in all_participants] + [0])
            auto_number = max_number + 1

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

    # Tab 3: Import Excel/CSV with Edit
    with tab3:
        st.markdown("### Import Excel/CSV")

        st.markdown("""
        Upload **Excel (.xlsx)** or **CSV** file to import participants.

        - Data will be converted to CSV format
        - Edit data directly in the table
        - Preview and save to database
        """)

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload File",
            type=["xlsx", "xls", "csv"],
            help="Select Excel or CSV file",
        )

        if uploaded_file:
            try:
                import pandas as pd
                import openpyxl
                from io import BytesIO

                file_type = uploaded_file.name.split(".")[-1].lower()
                file_name = uploaded_file.name.split(".")[0]

                # Load data
                if file_type == "csv":
                    try:
                        df = pd.read_csv(uploaded_file)
                    except:
                        df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
                else:
                    # Use pandas to read Excel - simpler approach
                    try:
                        df = pd.read_excel(BytesIO(uploaded_file.read()), sheet_name=0)
                    except:
                        wb = openpyxl.load_workbook(
                            BytesIO(uploaded_file.read()), data_only=True
                        )
                        ws = wb.active
                        headers = [
                            str(cell.value) if cell.value else f"col_{i}"
                            for i, cell in enumerate(ws[1], 1)
                        ]
                        rows_data = [
                            list(row)
                            for row in ws.iter_rows(min_row=2, values_only=True)
                        ]
                        df = (
                            pd.DataFrame(
                                rows_data, columns=headers[: len(rows_data[0])]
                            )
                            if rows_data
                            else pd.DataFrame()
                        )

                # Convert to CSV format name
                csv_name = f"{file_name}.csv"

                st.success(f"Loaded: {uploaded_file.name} → {csv_name}")
                st.info(f"Total rows: {len(df)}")

                if not df.empty:
                    # Column mapping
                    st.markdown("### Column Mapping")
                    col1, col2 = st.columns(2)

                    with col1:
                        # Auto-detect commander_id column
                        id_candidates = [
                            c
                            for c in df.columns
                            if any(
                                x in str(c).lower()
                                for x in ["commander", "id", "igg", "number"]
                            )
                        ]
                        id_col = st.selectbox(
                            "Commander ID Column",
                            options=list(df.columns),
                            index=list(df.columns).index(id_candidates[0])
                            if id_candidates
                            else 0,
                        )

                    with col2:
                        nickname_col = st.selectbox(
                            "Nickname Column (Optional)",
                            options=["None"] + list(df.columns),
                            index=0,
                        )

                    # Apply column mapping
                    if id_col:
                        df_mapped = pd.DataFrame()
                        df_mapped["commander_id"] = df[id_col].astype(str)

                        if nickname_col != "None":
                            df_mapped["nickname"] = df[nickname_col].astype(str)

                        # Auto-fill other columns
                        for col in df.columns:
                            if col != id_col and col != nickname_col:
                                col_clean = str(col).lower().strip().replace(" ", "_")
                                df_mapped[col_clean] = df[col].astype(str)

                        # Event name
                        event_name = st.text_input(
                            "Event Name",
                            placeholder="e.g., 260128",
                            value=file_name.split("_")[0] if "_" in file_name else "",
                        )
                        if event_name:
                            df_mapped["event_name"] = event_name

                        st.markdown("---")
                        st.markdown("### 📊 Edit Data")

                        # Show editable dataframe
                        edited_df = st.data_editor(
                            df_mapped,
                            num_rows="dynamic",
                            use_container_width=True,
                            key="participant_editor",
                        )

                        st.markdown("---")

                        # Action buttons
                        col_btn1, col_btn2 = st.columns(2)

                        with col_btn1:
                            if st.button(
                                "💾 Save to Database",
                                type="primary",
                                use_container_width=True,
                            ):
                                if not event_name:
                                    st.error("Enter event name.")
                                else:
                                    with st.spinner("Saving..."):
                                        saved_count = 0
                                        for idx, row in edited_df.iterrows():
                                            try:
                                                row_data = row.to_dict()
                                                if (
                                                    row_data.get("commander_id")
                                                    and row_data.get("commander_id")
                                                    != "nan"
                                                ):
                                                    db.add_participant(row_data)
                                                    saved_count += 1
                                            except Exception as e:
                                                st.warning(f"Row {idx}: {e}")
                                                continue

                                        st.success(f"Saved {saved_count} records!")
                                        st.rerun()

                        with col_btn2:
                            # Download as CSV
                            csv_data = edited_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv_data,
                                csv_name,
                                "text/csv",
                                use_container_width=True,
                            )
                    else:
                        st.error("Please select Commander ID column.")
                else:
                    st.warning("No data found in file.")

            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("""
    ### Admin Guide

    - **Participants List**: View and edit participant info
    - **Add Participant**: Manually add new participant
    - **Import Excel/CSV**: Bulk import from file

    **Supported Column Keywords:**
    - **Commander ID**: commander_id, commander, number, id, igg_id
    - **Nickname**: nickname, name
    - **Affiliation**: affiliation, guild
    - **Alliance**: alliance
    - **Notes**: notes, comment
    """)
