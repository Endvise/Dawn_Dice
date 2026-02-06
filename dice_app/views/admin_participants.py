#!/usr/bin/env python3
"""
Admin Participants Management Page
- Excel upload with auto ID/password generation
- Bulk operations: add to session, add to reservations
- Participant status management
"""

import streamlit as st
import pandas as pd
import openpyxl
import secrets
import string
import re
from io import BytesIO
import database as db
import auth


def generate_password(length: int = 12) -> str:
    """Generate random password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def show():
    """Show participants management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    # Get current active session
    active_session = db.get_active_session()

    st.title("Participants Management")
    st.markdown("---")

    # Session info
    if active_session:
        st.info(
            f"**Current Session**: {active_session.get('session_number', 'N/A')} - {active_session.get('session_name', 'N/A')}"
        )
    else:
        st.warning("No active session. Create a session first to link participants.")

    # Statistics
    participants = db.list_participants()
    users = db.list_users()
    reservations = db.list_reservations()

    total_participants = len(participants)
    completed_participants = len([p for p in participants if p.get("completed")])
    registered_this_session = len(
        [
            p
            for p in participants
            if p.get("event_name")
            == (active_session.get("session_name") if active_session else None)
        ]
    )

    # Get unique commander numbers from reservations
    reservation_commander_ids = set(r.get("commander_number") for r in reservations)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Participants", f"{total_participants}")

    with col2:
        st.metric("Completed", f"{completed_participants}")

    with col3:
        st.metric("This Session", f"{registered_this_session}")

    with col4:
        st.metric("Reservations", f"{len(reservations)}")

    st.markdown("---")

    # ===== TABS: Clear 5-tab structure =====
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["👥 Participants", "➕ Add", "📋 Reservations", "📥 Import Excel", "👤 Users"]
    )

    # ========== Tab 1: Participants List ==========
    with tab1:
        st.markdown("### 👥 Participants")

        col1, col2, col3 = st.columns(3)

        with col1:
            event_filter = st.text_input(
                "Event Filter", placeholder="e.g., 260128", key="p_event_filter"
            )

        with col2:
            status_filter = st.selectbox(
                "Status",
                ["All", "Registered This Session", "Pending", "Completed"],
                key="p_status_filter",
            )

        with col3:
            search_term = st.text_input(
                "Search", placeholder="Nickname/Commander ID", key="p_search"
            )

        # Get current session name
        current_session_name = (
            active_session.get("session_name") if active_session else None
        )

        # Filter participants
        filtered_participants = []
        for p in participants:
            # Event filter
            if event_filter and event_filter not in (p.get("event_name") or ""):
                continue

            # Status filter
            p_event = p.get("event_name") or ""
            is_registered_this_session = (
                current_session_name and p_event == current_session_name
            )
            is_completed = p.get("completed")

            if (
                status_filter == "Registered This Session"
                and not is_registered_this_session
            ):
                continue
            if status_filter == "Pending" and is_registered_this_session:
                continue
            if status_filter == "Completed" and not is_completed:
                continue

            # Search filter
            if search_term:
                search_lower = search_term.lower()
                if search_lower not in (
                    p.get("nickname") or ""
                ).lower() and search_lower not in str(p.get("igg_id", "")):
                    continue

            filtered_participants.append(p)

        st.markdown(f"### Participants ({len(filtered_participants)})")

        if filtered_participants:
            # Edit mode
            edit_id = st.session_state.get("edit_participant_id")

            if edit_id:
                participant = db.fetch_one("participants", {"id": f"eq.{edit_id}"})
                if participant:
                    _show_edit_form(participant, is_master)
            else:
                # Display list
                _display_participants_list(
                    filtered_participants, is_master, current_session_name
                )
        else:
            st.info("No participants found.")

    # ========== Tab 2: Add Participants ==========
    with tab2:
        st.markdown("### ➕ Add Participants")

        if not active_session:
            st.warning("No active session. Create a session first.")
        else:
            # Nested tabs: New Participant / From Previous Session
            tab2_1, tab2_2 = st.tabs(["✨ New Participant", "📥 From Previous Session"])

            # ----- Tab 2-1: Add New Participant -----
            with tab2_1:
                st.markdown(
                    f"**Add to Session**: {active_session.get('session_name', 'N/A')}"
                )

                with st.form("add_participant_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_nickname = st.text_input("Nickname *", key="new_nickname")
                        new_commander_id = st.text_input(
                            "Commander ID * (10 digits)", key="new_commander_id"
                        )
                    with col2:
                        new_server = st.text_input("Server *", key="new_server")
                        new_alliance = st.text_input(
                            "Alliance (Optional)", key="new_alliance"
                        )

                    st.markdown("---")
                    if st.form_submit_button(
                        "➕ Add Participant", type="primary", use_container_width=True
                    ):
                        if not new_commander_id or not new_nickname or not new_server:
                            st.error("Please fill in all required fields (*)")
                        elif (
                            len(new_commander_id) != 10
                            or not new_commander_id.isdigit()
                        ):
                            st.error("Commander ID must be 10 digits")
                        else:
                            # Check if user exists
                            existing = db.get_user_by_commander_number(new_commander_id)
                            if existing:
                                st.info(
                                    "Existing user found. Will add to participants with existing info."
                                )
                                nickname = existing.get("nickname", "")
                                server = existing.get("server", "")
                                alliance = existing.get("alliance", "")
                            else:
                                # Create new user
                                password = generate_password()
                                password_hash = db.hash_password(password)
                                user_data = {
                                    "commander_number": new_commander_id,
                                    "nickname": new_nickname,
                                    "password_hash": password_hash,
                                    "plaintext_password": password,
                                    "server": new_server,
                                    "alliance": new_alliance if new_alliance else None,
                                    "is_active": True,
                                }
                                user_id = db.insert("users", user_data)
                                nickname = new_nickname
                                server = new_server
                                alliance = new_alliance if new_alliance else None
                                st.success(f"New user created! Password: {password}")

                            # Add to participants
                            participant_data = {
                                "nickname": nickname,
                                "igg_id": new_commander_id,
                                "affiliation": server,
                                "alliance": alliance,
                                "event_name": active_session.get("session_name"),
                                "completed": 0,
                                "confirmed": 0,
                                "wait_confirmed": 0,
                                "notes": f"Added by admin - {user.get('username', 'admin')}",
                            }
                            db.add_participant(participant_data)
                            st.success("Participant added!")
                            st.rerun()

            # ----- Tab 2-2: From Previous Session -----
            with tab2_2:
                st.markdown("#### Import from Previous Session")

                # Get all sessions except current
                all_sessions = db.fetch_all("event_sessions")
                session_names = [
                    s.get("session_name")
                    for s in all_sessions
                    if s.get("session_name")
                    and s.get("session_name") != current_session_name
                ]

                if not session_names:
                    st.info("No previous sessions found.")
                else:
                    prev_session = st.selectbox(
                        "Select Previous Session", session_names
                    )

                    if prev_session:
                        prev_participants = [
                            p
                            for p in participants
                            if p.get("event_name") == prev_session
                        ]

                        if not prev_participants:
                            st.info(f"No participants in {prev_session}")
                        else:
                            st.markdown(
                                f"**Found {len(prev_participants)} participants**"
                            )

                            # Select all
                            select_all_prev = st.checkbox(
                                "Select All", key="select_all_prev"
                            )

                            selected_prev = []
                            for p in prev_participants:
                                col_cb, col_info = st.columns([1, 4])
                                with col_cb:
                                    if st.checkbox(
                                        "",
                                        key=f"prev_{p.get('id')}",
                                        value=select_all_prev,
                                    ):
                                        selected_prev.append(p.get("id"))
                                with col_info:
                                    st.markdown(
                                        f"**{p.get('nickname', 'Unknown')}** - {p.get('igg_id', 'N/A')}"
                                    )

                            st.markdown("---")
                            if st.button(
                                "Add Selected to Current Session", type="primary"
                            ):
                                if not selected_prev:
                                    st.error("No participants selected.")
                                else:
                                    added = 0
                                    for p in prev_participants:
                                        if p.get("id") in selected_prev:
                                            try:
                                                # Get user info
                                                user = db.get_user_by_commander_number(
                                                    p.get("igg_id", "")
                                                )
                                                nickname = (
                                                    user.get("nickname", "")
                                                    if user
                                                    else p.get("nickname", "")
                                                )
                                                server = (
                                                    user.get("server", "")
                                                    if user
                                                    else p.get("affiliation", "")
                                                )
                                                alliance = (
                                                    user.get("alliance", "")
                                                    if user
                                                    else p.get("alliance", "")
                                                )

                                                db.add_participant(
                                                    {
                                                        "nickname": nickname,
                                                        "igg_id": p.get("igg_id", ""),
                                                        "affiliation": server,
                                                        "alliance": alliance,
                                                        "event_name": current_session_name,
                                                        "completed": 0,
                                                        "confirmed": 0,
                                                        "wait_confirmed": 0,
                                                        "notes": f"Imported from {prev_session}",
                                                    }
                                                )
                                                added += 1
                                            except Exception as e:
                                                st.error(f"Error: {e}")
                                    st.success(f"Added {added} participants!")
                                    st.rerun()

    # ========== Tab 3: Reservations ==========
    with tab3:
        st.markdown("### 📋 Reservations")

        if not active_session:
            st.warning("No active session.")
        else:
            st.markdown(f"**Session**: {active_session.get('session_name', 'N/A')}")

            # Get participants in current session
            session_participants = [
                p for p in participants if p.get("event_name") == current_session_name
            ]

            if not session_participants:
                st.info("No participants in this session.")
            else:
                # Separate by reservation status
                in_reservation = []
                not_in_reservation = []

                for p in session_participants:
                    if p.get("igg_id") in reservation_commander_ids:
                        in_reservation.append(p)
                    else:
                        not_in_reservation.append(p)

                col_r1, col_r2 = st.columns(2)

                with col_r1:
                    st.markdown(f"**✅ In Reservation ({len(in_reservation)})**")
                    for p in in_reservation:
                        with st.container(border=True):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.markdown(
                                    f"**{p.get('nickname', 'Unknown')}** - {p.get('igg_id', 'N/A')}"
                                )
                            with col_b:
                                if st.button(
                                    "❌",
                                    key=f"cancel_res_{p.get('id')}",
                                    help="Cancel reservation",
                                ):
                                    st.error("Cancel functionality to be implemented")

                with col_r2:
                    st.markdown(
                        f"**⏳ Not in Reservation ({len(not_in_reservation)})**"
                    )
                    select_all_res = st.checkbox(
                        "Select All", key="select_all_reservation"
                    )

                    selected_ids = []
                    for p in not_in_reservation:
                        col_cb, col_info = st.columns([1, 4])
                        with col_cb:
                            if st.checkbox(
                                "", key=f"res_{p.get('id')}", value=select_all_res
                            ):
                                selected_ids.append(p.get("id"))
                        with col_info:
                            st.markdown(
                                f"**{p.get('nickname', 'Unknown')}** - {p.get('igg_id', 'N/A')}"
                            )

                    st.markdown("---")
                    if st.button(
                        "Add Selected to Reservations",
                        type="primary",
                        use_container_width=True,
                    ):
                        if not selected_ids:
                            st.error("No participants selected.")
                        else:
                            added = 0
                            for p in not_in_reservation:
                                if p.get("id") in selected_ids:
                                    try:
                                        # Get user info
                                        user_info = db.get_user_by_commander_number(
                                            p.get("igg_id", "")
                                        )
                                        db.create_reservation(
                                            user_id=user_info.get("id")
                                            if user_info
                                            else None,
                                            nickname=p.get("nickname", ""),
                                            commander_number=p.get("igg_id", ""),
                                            server=p.get("affiliation", ""),
                                            notes=f"Pre-registered by admin - {user.get('username', 'admin')}",
                                        )
                                        added += 1
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            st.success(f"Added {added} to reservations!")
                            st.rerun()

    # ========== Tab 4: Import Excel ==========
    with tab4:
        st.markdown("### 📥 Import Excel")

        st.markdown("""
        **Excel Format:**
        - **Commander ID**: 10-digit number (required)
        - **Affiliation**: `#000 alliance_name` format → server(#000) + alliance name
        - **Nickname**: Leave blank (user will change later)
        - **Deduplication**: If commander ID is duplicated, only 1 entry is kept
        """)

        # Session selection
        event_names = [p.get("event_name") for p in participants if p.get("event_name")]
        session_options = ["Select Session..."] + sorted(set(event_names))
        if active_session:
            default_idx = (
                session_options.index(active_session.get("session_name")) + 1
                if active_session.get("session_name") in session_options
                else 0
            )
        else:
            default_idx = 0

        import_session = st.selectbox(
            "Event/Session", session_options, index=default_idx, key="import_session"
        )

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload Excel File",
            type=["xlsx", "xls"],
            help="Required: Commander ID column (10 digits). Affiliation format: '#000 alliance_name'",
        )

        if uploaded_file:
            try:
                df = pd.read_excel(BytesIO(uploaded_file.read()), sheet_name=0)

                st.success(f"Loaded: {uploaded_file.name} - {len(df)} rows")

                # Column selection
                st.markdown("### Column Mapping")
                col1, col2 = st.columns(2)

                all_cols = list(df.columns)

                with col1:
                    commander_id_col = st.selectbox(
                        "Commander ID Column (10 digits)",
                        all_cols,
                        index=0,
                        help="Column containing 10-digit commander ID",
                    )

                with col2:
                    affiliation_col = st.selectbox(
                        "Affiliation Column",
                        ["None"] + all_cols,
                        index=1 if len(all_cols) > 1 else 0,
                        help="Affiliation column in '#000 alliance_name' format",
                    )

                # Process and show preview
                st.markdown("### Preview (Processed)")

                # Process data
                processed_data = []
                seen_commander_ids = set()
                duplicate_ids = []
                invalid_ids = []

                for idx, row in df.iterrows():
                    # Extract commander ID (10 digits)
                    raw_id = str(row.get(commander_id_col, "")).strip()

                    match = re.search(r"\d{10}", raw_id)
                    if match:
                        commander_id = match.group()
                    else:
                        # Track invalid IDs
                        invalid_ids.append(
                            {
                                "row": idx + 1,
                                "value": raw_id[:50] if raw_id else "(빈 값)",
                            }
                        )
                        continue

                    # Remove duplicates
                    if commander_id in seen_commander_ids:
                        duplicate_ids.append(
                            {
                                "row": idx + 1,
                                "id": commander_id,
                            }
                        )
                        continue
                    seen_commander_ids.add(commander_id)

                    # Parse affiliation: "#000 alliance_name"
                    server = ""
                    alliance = ""
                    if affiliation_col != "None" and pd.notna(row.get(affiliation_col)):
                        raw_aff = str(row[affiliation_col]).strip()
                        # Split by space, first part is server (#000), rest is alliance
                        parts = raw_aff.split(" ", 1)
                        server = parts[0] if parts else ""
                        alliance = parts[1] if len(parts) > 1 else ""

                    processed_data.append(
                        {
                            "commander_id": commander_id,
                            "nickname": "",  # Empty - user will set later
                            "server": server,
                            "alliance": alliance,
                        }
                    )

                if not processed_data:
                    st.warning("No valid commander IDs found (10 digits required).")
                else:
                    preview_df = pd.DataFrame(processed_data)

                    # Show all data
                    st.dataframe(preview_df, use_container_width=True)

                    # Show debug info with expandable details
                    col_debug1, col_debug2, col_debug3 = st.columns(3)
                    with col_debug1:
                        st.info(f"**총 행 수**: {len(df)}")
                    with col_debug2:
                        st.warning(f"**중복 제거됨**: {len(duplicate_ids)}개")
                        if duplicate_ids:
                            with st.expander("중복 ID 목록"):
                                dup_df = pd.DataFrame(duplicate_ids)
                                st.dataframe(dup_df, use_container_width=True)
                    with col_debug3:
                        st.error(f"**유효하지 않은 ID**: {len(invalid_ids)}개")
                        if invalid_ids:
                            with st.expander("유효하지 않은 ID 목록"):
                                invalid_df = pd.DataFrame(invalid_ids)
                                st.dataframe(invalid_df, use_container_width=True)

                    st.info(f"**최종 유효 항목**: {len(processed_data)}개")

                    # Import button
                    if st.button(
                        "Import with Auto-generated Credentials",
                        type="primary",
                        use_container_width=True,
                    ):
                        if import_session == "Select Session...":
                            st.error("Please select a session.")
                        elif not processed_data:
                            st.error("No valid data to import.")
                        else:
                            with st.spinner("Importing..."):
                                success_count = 0
                                password_report = []

                            for data in processed_data:
                                try:
                                    commander_id = data["commander_id"]
                                    server = data["server"]
                                    alliance = data["alliance"]

                                    # Generate password
                                    password = generate_password()
                                    password_hash = db.hash_password(password)

                                    # Check if user exists
                                    existing_user = db.get_user_by_commander_number(
                                        commander_id
                                    )

                                    if existing_user:
                                        user_id = existing_user["id"]
                                        action = "existing"
                                        # Use existing user info
                                        nickname = existing_user.get("nickname", "")
                                        user_server = existing_user.get("server", "")
                                        user_alliance = existing_user.get(
                                            "alliance", ""
                                        )
                                        # Store plaintext password if not exists
                                        if not existing_user.get("plaintext_password"):
                                            try:
                                                db.update(
                                                    "users",
                                                    {"plaintext_password": password},
                                                    {"id": f"eq.{user_id}"},
                                                )
                                            except:
                                                pass
                                    else:
                                        # Create new user
                                        user_data = {
                                            "commander_number": commander_id,
                                            "nickname": nickname,  # Use nickname from form
                                            "password_hash": password_hash,
                                            "plaintext_password": password,
                                            "server": server,
                                            "alliance": alliance,
                                            "is_active": True,
                                        }
                                        user_id = db.insert("users", user_data)
                                        action = "new"
                                        nickname = ""
                                        user_server = server
                                        user_alliance = alliance

                                    # Add to participants - use existing user info
                                    participant_data = {
                                        "nickname": nickname,  # ✅ Existing user's nickname
                                        "igg_id": commander_id,
                                        "affiliation": user_server,  # ✅ Existing user's server
                                        "alliance": user_alliance,  # ✅ Existing user's alliance
                                        "event_name": import_session,
                                        "completed": 0,
                                        "confirmed": 0,
                                        "wait_confirmed": 0,
                                        "notes": f"Imported by {user.get('username', 'admin')}",
                                    }
                                    db.add_participant(participant_data)

                                    success_count += 1
                                    password_report.append(
                                        {
                                            "Commander ID": commander_id,
                                            "Server": server,
                                            "Alliance": alliance,
                                            "Password": password,
                                            "Status": action.capitalize(),
                                        }
                                    )

                                except Exception as e:
                                    st.warning(
                                        f"Error importing {data.get('commander_id', 'unknown')}: {e}"
                                    )
                                    continue

                            st.success(f"Imported {success_count} participants!")

                            # Show password report
                            if password_report:
                                st.markdown("### Credentials Report")
                                report_df = pd.DataFrame(password_report)
                                st.dataframe(report_df, use_container_width=True)

                                # Download report
                                csv = report_df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download Credentials CSV",
                                    csv,
                                    f"credentials_{import_session}.csv",
                                    "text/csv",
                                    use_container_width=True,
                                )

                            st.rerun()

            except Exception as e:
                st.error(f"Error reading file: {e}")

    # ========== Tab 5: Users ==========
    with tab5:
        st.markdown("### 👤 User Accounts")

        st.markdown("""
        View and manage user accounts created from participant imports.
        - View plaintext passwords for distribution
        - Reset passwords if needed
        """)

        if users:
            search_user = st.text_input(
                "Search User", placeholder="Nickname/Commander ID", key="search_user"
            )

            filtered_users = []
            for u in users:
                if search_user:
                    search_lower = search_user.lower()
                    if (
                        search_lower not in (u.get("nickname") or "").lower()
                        and search_lower
                        not in (u.get("commander_number") or "").lower()
                    ):
                        continue
                filtered_users.append(u)

            st.markdown(f"**Users ({len(filtered_users)})**")

            show_all = st.checkbox(
                "Show All Passwords", value=False, key="show_all_passwords"
            )

            for u in filtered_users[:50]:
                user_id = str(u.get("id", ""))
                show_pw = st.session_state.get(f"show_pw_{user_id}", False)
                if show_all:
                    show_pw = True

                with st.expander(
                    f"{u.get('nickname', 'Unknown')} - {u.get('commander_number', 'N/A')}"
                ):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.markdown(f"**Nickname**: {u.get('nickname', 'Unknown')}")
                        st.markdown(
                            f"**Commander ID**: {u.get('commander_number', 'N/A')}"
                        )
                        st.markdown(f"**Server**: {u.get('server', 'N/A')}")
                        st.markdown(
                            f"**Alliance**: {u.get('alliance', 'N/A') if u.get('alliance') else 'None'}"
                        )

                    with col2:
                        status = "Active" if u.get("is_active") else "Inactive"
                        st.markdown(f"**Status**: {status}")
                        st.markdown(
                            f"**Created**: {str(u.get('created_at', 'N/A'))[:10]}"
                        )

                        if u.get("plaintext_password"):
                            col_pw, col_toggle = st.columns([3, 1])
                            with col_pw:
                                pw_value = (
                                    u.get("plaintext_password", "")
                                    if show_pw
                                    else "••••••••••••"
                                )
                                st.text_input(
                                    "Password",
                                    value=pw_value,
                                    type="default" if show_pw else "password",
                                    disabled=True,
                                    key=f"pw_{user_id}",
                                )
                            with col_toggle:
                                if st.button(
                                    "Show" if not show_pw else "Hide",
                                    key=f"toggle_{user_id}",
                                ):
                                    st.session_state[f"show_pw_{user_id}"] = not show_pw
                                    st.rerun()
                        else:
                            st.warning("No password stored")

                        if st.button(
                            "Reset Password",
                            key=f"reset_{user_id}",
                            use_container_width=True,
                        ):
                            new_pw = generate_password()
                            new_hash = db.hash_password(new_pw)
                            db.update(
                                "users",
                                {
                                    "password_hash": new_hash,
                                    "plaintext_password": new_pw,
                                },
                                {"id": f"eq.{user_id}"},
                            )
                            st.success(f"Reset! {new_pw}")
                            st.rerun()

            if any(u.get("plaintext_password") for u in filtered_users):
                all_creds = [
                    {
                        "Nickname": u.get("nickname", ""),
                        "ID": u.get("commander_number", ""),
                        "Password": u.get("plaintext_password", ""),
                        "Server": u.get("server", ""),
                        "Alliance": u.get("alliance", ""),
                    }
                    for u in filtered_users
                    if u.get("plaintext_password")
                ]
                if all_creds:
                    st.download_button(
                        "Download All",
                        pd.DataFrame(all_creds).to_csv(index=False),
                        "creds.csv",
                        "text/csv",
                        use_container_width=True,
                    )
        else:
            st.info("No user accounts yet.")

    st.markdown("---")


def _show_edit_form(participant: dict, is_master: bool):
    """Show participant edit form."""
    st.markdown("### Edit Participant")

    col1, col2 = st.columns(2)

    with col1:
        number = st.number_input(
            "Number",
            min_value=1,
            value=int(participant.get("number", 1)),
        )
        nickname = st.text_input("Nickname", value=participant.get("nickname", ""))
        igg_id = st.text_input("IGG ID", value=participant.get("igg_id", "") or "")
        affiliation = st.text_input(
            "Affiliation", value=participant.get("affiliation", "") or ""
        )
        alliance = st.text_input(
            "Alliance", value=participant.get("alliance", "") or ""
        )
        event_name = st.text_input(
            "Event Name", value=participant.get("event_name", "") or ""
        )

    with col2:
        wait_confirmed = st.checkbox(
            "Wait Confirmed", value=bool(participant.get("wait_confirmed"))
        )
        confirmed = st.checkbox("Confirmed", value=bool(participant.get("confirmed")))
        completed = st.checkbox("Completed", value=bool(participant.get("completed")))
        notes = st.text_area(
            "Notes", value=participant.get("notes", "") or "", height=100
        )

    st.markdown("---")

    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("Save Changes", type="primary", use_container_width=True):
            try:
                db.update_participant(
                    participant["id"],
                    number=number,
                    nickname=nickname,
                    igg_id=igg_id if igg_id else None,
                    affiliation=affiliation if affiliation else None,
                    alliance=alliance if alliance else None,
                    event_name=event_name if event_name else None,
                    wait_confirmed=1 if wait_confirmed else 0,
                    confirmed=1 if confirmed else 0,
                    completed=1 if completed else 0,
                    notes=notes if notes else None,
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
            if st.button("Delete", type="secondary", use_container_width=True):
                try:
                    db.delete_participant(participant["id"])
                    st.success("Deleted!")
                    st.session_state["edit_participant_id"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")


def _display_participants_list(
    participants: list, is_master: bool, current_session_name: str = None
):
    """Display participants list."""
    for p in participants:
        p_event = p.get("event_name") or ""
        is_in_current_session = current_session_name and p_event == current_session_name

        # Status badge
        if p.get("completed"):
            badge = "✅ Completed"
        elif is_in_current_session:
            badge = "🎯 This Session"
        else:
            badge = "⏳ Pending"

        with st.expander(
            f"{badge} {p.get('nickname', 'Unknown')} - {p.get('igg_id', 'N/A')}"
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Nickname**: {p.get("nickname", "Unknown")}
                **IGG ID**: {p.get("igg_id", "N/A")}
                **Affiliation**: {p.get("affiliation", "N/A")}
                **Alliance**: {p.get("alliance", "N/A") if p.get("alliance") else "None"}
                **Event**: {p_event or "Not assigned"}
                **Notes**: {p.get("notes", "N/A")}
                """)

            with col2:
                status_flags = []
                if p.get("confirmed"):
                    status_flags.append("✅ Confirmed")
                if p.get("wait_confirmed"):
                    status_flags.append("⏳ Wait Confirmed")
                if p.get("completed"):
                    status_flags.append("🎉 Completed")

                for flag in status_flags:
                    st.markdown(f"- {flag}")

            # Actions
            col_act1, col_act2 = st.columns(2)

            with col_act1:
                if st.button("Edit", key=f"edit_{p['id']}", use_container_width=True):
                    st.session_state["edit_participant_id"] = p["id"]
                    st.rerun()

            with col_act2:
                if is_master:
                    if st.button(
                        "Delete",
                        key=f"delete_{p['id']}",
                        type="secondary",
                        use_container_width=True,
                    ):
                        try:
                            db.delete_participant(p["id"])
                            st.success("Deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
