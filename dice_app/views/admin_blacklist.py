#!/usr/bin/env python3
"""
Admin Blacklist Management Page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show blacklist management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Blacklist Management")
    st.markdown("---")

    # Statistics
    local_blacklist = db.list_blacklist()
    total_blacklisted = len(local_blacklist)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Local Blacklist", f"{total_blacklisted}")

    with col2:
        st.info("Google Sheets blacklist is also checked automatically.")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Blacklist List", "Add to Blacklist", "Upload from File", "Inactive List"]
    )

    # Tab 1: Blacklist list with editing
    with tab1:
        st.markdown("### Active Blacklist")

        # Edit mode check
        edit_id = st.session_state.get("edit_blacklist_id")

        if edit_id:
            # Show edit form
            blacklist_entry = db.fetch_one("blacklist", {"id": f"eq.{edit_id}"})
            if blacklist_entry:
                st.markdown("### Edit Blacklist Entry")
                col1, col2 = st.columns(2)

                with col1:
                    commander_id = st.text_input(
                        "Commander ID",
                        value=blacklist_entry.get("commander_id", ""),
                    )
                    nickname = st.text_input(
                        "Nickname",
                        value=blacklist_entry.get("nickname", "") or "",
                    )
                    reason = st.text_area(
                        "Reason",
                        value=blacklist_entry.get("reason", "") or "",
                        height=100,
                    )

                with col2:
                    st.markdown("### Guide")
                    st.markdown("""
                    - **Commander ID**: 10-digit number (required)
                    - **Nickname**: Optional
                    - **Reason**: Reason for blacklist (required)
                    """)

                st.markdown("---")

                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if st.button(
                        "Save Changes", type="primary", use_container_width=True
                    ):
                        try:
                            db.update(
                                "blacklist",
                                {
                                    "commander_id": commander_id,
                                    "nickname": nickname if nickname else None,
                                    "reason": reason if reason else None,
                                },
                                {"id": f"eq.{edit_id}"},
                            )
                            st.success("Updated successfully!")
                            st.session_state["edit_blacklist_id"] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                with col_btn2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state["edit_blacklist_id"] = None
                        st.rerun()

                with col_btn3:
                    if st.button(
                        "Deactivate", type="secondary", use_container_width=True
                    ):
                        try:
                            db.remove_from_blacklist(commander_id)
                            st.success("Deactivated!")
                            st.session_state["edit_blacklist_id"] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                st.markdown("---")

        if local_blacklist:
            for bl in local_blacklist:
                with st.expander(
                    f"🚫 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"""
                        **Commander ID**: {bl["commander_id"]}
                        **Nickname**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                        **Reason**: {bl["reason"] if bl["reason"] else "N/A"}
                        **Added At**: {bl["added_at"]}
                        """)

                        if bl.get("added_by"):
                            adder = db.get_user_by_id(bl["added_by"])
                            if adder:
                                st.info(
                                    f"Added by: {adder.get('nickname', adder.get('username', 'Unknown'))}"
                                )

                    with col2:
                        st.markdown("### Actions")

                        if st.button(
                            "Edit",
                            key=f"edit_{bl['id']}",
                            use_container_width=True,
                        ):
                            st.session_state["edit_blacklist_id"] = bl["id"]
                            st.rerun()

                        if st.button(
                            "Deactivate",
                            key=f"deactivate_{bl['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.remove_from_blacklist(bl["commander_id"])
                                st.success("Removed from blacklist.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error removing: {e}")
        else:
            st.info("No active blacklist entries.")

    # Tab 2: Add to blacklist
    with tab2:
        st.markdown("### Add to Blacklist")

        col1, col2 = st.columns([1, 2])

        with col1:
            commander_id = st.text_input("Commander ID", placeholder="10-digit number")

            if commander_id:
                existing = db.check_blacklist(commander_id)
                if existing:
                    st.error(
                        f"Already on blacklist. (Reason: {existing.get('reason', 'N/A')})"
                    )
                else:
                    st.success("New Commander ID.")

            nickname = st.text_input("Nickname", placeholder="Optional")
            reason = st.text_area(
                "Blacklist Reason", placeholder="Required", height=100
            )

        with col2:
            st.markdown("### Guide")

            st.markdown("""
            - **Commander ID**: 10-digit number (required)
            - **Nickname**: Optional
            - **Reason**: Reason for blacklist (required)

            Users on blacklist:
            - Cannot make reservations
            - Cannot register
            - Existing reservations cancelled automatically
            """)

        st.markdown("---")
        if st.button("Add to Blacklist", type="primary", use_container_width=True):
            if not commander_id:
                st.error("Enter Commander ID.")
                return

            if not reason:
                st.error("Enter blacklist reason.")
                return

            try:
                db.add_to_blacklist(
                    commander_id=commander_id,
                    nickname=nickname if nickname else None,
                    reason=reason,
                    added_by=user["id"],
                )

                st.success(f"{commander_id} added to blacklist.")

                affected_reservations = db.list_reservations()
                affected_count = len(
                    [
                        r
                        for r in affected_reservations
                        if r["commander_id"] == commander_id
                    ]
                )

                if affected_count > 0:
                    st.warning(f"{affected_count} reservations affected.")

                st.rerun()

            except Exception as e:
                st.error(f"Error adding: {e}")

    # Tab 3: Upload from file
    with tab3:
        st.markdown("### Upload Blacklist from File")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("#### Supported File Formats")

            st.info("""
            **Supported Formats:**
            - **CSV**: Comma-separated values
            - **Excel**: .xlsx, .xls files
            - **TXT**: Tab or comma-separated text

            **Required Column:**
            - `commander_id` or `id` or `igg_id` (required)
            - `nickname` (optional)
            - `reason` (optional, default: "Bulk upload")
            """)

            # File uploader
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["csv", "xlsx", "xls", "txt"],
                help="Upload CSV, Excel, or TXT file with blacklist entries",
            )

            # Column mapping
            st.markdown("#### Column Mapping")

            col_map1, col_map2, col_map3 = st.columns(3)

            with col_map1:
                id_column = st.text_input(
                    "ID Column Name",
                    value="commander_id",
                    help="Column name for Commander ID",
                )
            with col_map2:
                nickname_column = st.text_input(
                    "Nickname Column",
                    value="nickname",
                    help="Column name for nickname (optional)",
                )
            with col_map3:
                reason_column = st.text_input(
                    "Reason Column",
                    value="reason",
                    help="Column name for reason (optional)",
                )

            default_reason = st.text_input(
                "Default Reason",
                value="Bulk upload from file",
                help="Reason used if file doesn't have reason column",
            )

            st.markdown("---")

            if uploaded_file:
                if st.button("Process File", type="primary", use_container_width=True):
                    try:
                        import pandas as pd
                        from io import BytesIO

                        # Read file based on extension
                        file_ext = uploaded_file.name.split(".")[-1].lower()

                        if file_ext == "csv":
                            try:
                                df = pd.read_csv(uploaded_file, encoding="utf-8")
                            except UnicodeDecodeError:
                                try:
                                    df = pd.read_csv(
                                        uploaded_file, encoding="utf-8-sig"
                                    )
                                except UnicodeDecodeError:
                                    df = pd.read_csv(uploaded_file, encoding="cp949")
                        elif file_ext in ["xlsx", "xls"]:
                            df = pd.read_excel(uploaded_file)
                        elif file_ext == "txt":
                            # Try different delimiters
                            for delimiter in [",", "\t", "|"]:
                                try:
                                    df = pd.read_csv(
                                        uploaded_file, sep=delimiter, encoding="utf-8"
                                    )
                                    break
                                except:
                                    continue
                            else:
                                st.error(
                                    "Could not parse TXT file. Use comma, tab, or pipe as delimiter."
                                )
                                df = None

                        if df is not None:
                            # Normalize column names
                            df.columns = df.columns.str.strip().str.lower()

                            # Find ID column
                            id_col = None
                            for col in df.columns:
                                if (
                                    col == id_column.lower()
                                    or col == "id"
                                    or col.startswith("igg")
                                ):
                                    id_col = col
                                    break

                            if not id_col:
                                st.error(
                                    f"Could not find ID column '{id_column}' in file."
                                )
                            else:
                                # Extract data
                                entries = []
                                for idx, row in df.iterrows():
                                    commander_id = str(row.get(id_col, "")).strip()
                                    if commander_id and commander_id != "nan":
                                        nickname = (
                                            str(
                                                row.get(nickname_column.lower(), "")
                                            ).strip()
                                            if nickname_column
                                            else ""
                                        )
                                        if nickname == "nan":
                                            nickname = ""
                                        reason = (
                                            str(
                                                row.get(reason_column.lower(), "")
                                            ).strip()
                                            if reason_column
                                            else ""
                                        )
                                        if reason == "nan":
                                            reason = default_reason
                                        elif not reason:
                                            reason = default_reason

                                        entries.append(
                                            {
                                                "commander_id": commander_id,
                                                "nickname": nickname
                                                if nickname
                                                else None,
                                                "reason": reason,
                                            }
                                        )

                                if entries:
                                    st.session_state["pending_blacklist_entries"] = (
                                        entries
                                    )
                                    st.session_state["show_preview"] = True

                                    st.success(
                                        f"Found {len(entries)} entries. Preview below:"
                                    )
                                else:
                                    st.error("No valid entries found in file.")
                    except Exception as e:
                        st.error(f"Error processing file: {e}")

        with col2:
            st.markdown("#### Preview")

            # Initialize default reason with fallback
            _default_reason = (
                default_reason
                if "default_reason" in dir() or "default_reason" in locals()
                else "Bulk upload from file"
            )

            if "show_preview" in st.session_state and st.session_state.get(
                "show_preview"
            ):
                entries = st.session_state.get("pending_blacklist_entries", [])

                if entries:
                    # Show preview
                    preview_df = pd.DataFrame(entries[:10])
                    st.dataframe(preview_df, use_container_width=True)

                    if len(entries) > 10:
                        st.info(f"Showing first 10 of {len(entries)} entries")

                    st.markdown("---")

                    # Options
                    col_opt1, col_opt2 = st.columns(2)

                    with col_opt1:
                        skip_duplicates = st.checkbox(
                            "Skip existing blacklist entries",
                            value=True,
                            help="Skip Commander IDs already on blacklist",
                        )

                    with col_opt2:
                        st.markdown(f"**Total entries**: {len(entries)}")
                        if skip_duplicates:
                            # Count existing
                            existing_count = 0
                            for entry in entries:
                                existing = db.check_blacklist(entry["commander_id"])
                                if existing:
                                    existing_count += 1
                            st.info(f"**New entries**: {len(entries) - existing_count}")

                    st.markdown("---")

                    # Import button
                    if st.button(
                        "Import All to Blacklist",
                        type="primary",
                        use_container_width=True,
                    ):
                        imported_count = 0
                        skipped_count = 0
                        error_count = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for i, entry in enumerate(entries):
                            status_text.text(f"Processing {i + 1}/{len(entries)}...")
                            progress_bar.progress((i + 1) / len(entries))

                            # Check if should skip
                            if skip_duplicates:
                                existing = db.check_blacklist(entry["commander_id"])
                                if existing:
                                    skipped_count += 1
                                    continue

                            try:
                                # Safely get default_reason
                                _dr = (
                                    default_reason
                                    if "default_reason" in locals()
                                    or "default_reason" in globals()
                                    else "Bulk upload from file"
                                )
                                db.add_to_blacklist(
                                    commander_id=entry["commander_id"],
                                    nickname=entry.get("nickname"),
                                    reason=entry.get("reason", _dr),
                                    added_by=user["id"],
                                )
                                imported_count += 1
                            except Exception as e:
                                error_count += 1
                                st.warning(f"Error adding {entry['commander_id']}: {e}")

                        progress_bar.empty()
                        status_text.empty()

                        st.success(f"Import complete!")
                        st.info(f"- Imported: {imported_count}")
                        if skipped_count > 0:
                            st.info(f"- Skipped (existing): {skipped_count}")
                        if error_count > 0:
                            st.warning(f"- Errors: {error_count}")

                        # Clear session state
                        if "pending_blacklist_entries" in st.session_state:
                            del st.session_state["pending_blacklist_entries"]
                        if "show_preview" in st.session_state:
                            del st.session_state["show_preview"]

                        st.rerun()
            else:
                st.info("Upload a file to see preview here.")

    # Tab 4: Inactive list
    with tab4:
        st.markdown("### Inactive Blacklist")

        inactive_blacklist = db.list_blacklist(is_active=False)

        if inactive_blacklist:
            st.info(f"{len(inactive_blacklist)} inactive blacklist entries.")

            for bl in inactive_blacklist:
                with st.expander(
                    f"🔓 {bl['commander_id']} - {bl['nickname'] if bl['nickname'] else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **Commander ID**: {bl["commander_id"]}
                    **Nickname**: {bl["nickname"] if bl["nickname"] else "Unknown"}
                    **Reason**: {bl["reason"] if bl["reason"] else "N/A"}
                    **Added At**: {bl["added_at"]}
                    """)

                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:
                        if st.button(
                            "Restore",
                            key=f"restore_{bl['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.update(
                                    "blacklist",
                                    {"is_active": 1},
                                    {"id": f"eq.{bl['id']}"},
                                )
                                st.success("Blacklist restored.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error restoring: {e}")

                    with col_btn2:
                        if is_master:
                            if st.button(
                                "Delete Permanently",
                                key=f"permanent_delete_{bl['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                confirm_delete = st.checkbox(
                                    "I understand this cannot be undone",
                                    key=f"confirm_permanent_{bl['id']}",
                                )
                                if confirm_delete:
                                    try:
                                        db.delete("blacklist", {"id": f"eq.{bl['id']}"})
                                        st.success("Permanently deleted.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
        else:
            st.info("No inactive blacklist entries.")

    st.markdown("---")

    st.markdown("""
    ### Admin Guide

    - **Active**: Commander ID cannot reserve/register
    - **Deactivate**: Temporarily unblock (can be restored)
    - **Delete Permanently**: Complete removal (cannot restore)
    - **Google Sheets**: External blacklist is also checked automatically

    Only master accounts can permanently delete.
    """)
