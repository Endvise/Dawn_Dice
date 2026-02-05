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

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Participants List", "Add to Session", "Import Excel", "Manage Users"]
    )

    # ========== Tab 1: Participants List ==========
    with tab1:
        st.markdown("### Participants List")

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

    # ========== Tab 2: Add to Session ==========
    with tab2:
        st.markdown("### Add Participants to Session")

        if not active_session:
            st.warning("No active session. Create a session first.")
        else:
            st.info(
                f"Add participants to Session: **{active_session.get('session_name')}**"
            )

            # Get participants NOT in current session
            participants_not_in_session = [
                p for p in participants if p.get("event_name") != current_session_name
            ]

            if participants_not_in_session:
                st.markdown(
                    f"**{len(participants_not_in_session)}** participants available to add"
                )

                # Select all checkbox
                select_all = st.checkbox("Select All", key="select_all_not_in_session")

                # Session to add
                session_event_name = active_session.get("session_name")

                if st.button(
                    f"Add Selected to Session '{session_event_name}'", type="primary"
                ):
                    selected_ids = st.session_state.get("selected_participants", [])
                    if not selected_ids:
                        st.error("No participants selected.")
                    else:
                        added_count = 0
                        for p in participants_not_in_session:
                            if str(p.get("id")) in selected_ids or str(p.get("id")) in [
                                str(s) for s in selected_ids
                            ]:
                                try:
                                    db.update_participant(
                                        p["id"],
                                        event_name=session_event_name,
                                        completed=0,
                                        confirmed=0,
                                        wait_confirmed=0,
                                    )
                                    added_count += 1
                                except Exception as e:
                                    st.error(f"Error adding {p.get('nickname')}: {e}")
                        st.success(f"Added {added_count} participants to session!")
                        st.rerun()

                # Display participants not in session
                for p in participants_not_in_session:
                    col_cb, col_info = st.columns([1, 4])
                    with col_cb:
                        checked = st.checkbox(
                            "", key=f"select_{p.get('id')}", value=select_all
                        )
                        if checked:
                            if "selected_participants" not in st.session_state:
                                st.session_state["selected_participants"] = []
                            if (
                                str(p.get("id"))
                                not in st.session_state["selected_participants"]
                            ):
                                st.session_state["selected_participants"].append(
                                    str(p.get("id"))
                                )
                    with col_info:
                        st.markdown(
                            f"**{p.get('nickname', 'Unknown')}** - {p.get('igg_id', 'N/A')} - {p.get('affiliation', 'N/A')}"
                        )
            else:
                st.info("All participants are already in this session.")

        st.markdown("---")

        # ========== Add to Reservations ==========
        st.markdown("### Add to Reservations")

        if not active_session:
            st.warning("No active session.")
        else:
            st.info("Add approved participants to reservation list")

            # Get participants in current session
            session_participants = [
                p for p in participants if p.get("event_name") == current_session_name
            ]

            if session_participants:
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
                    st.markdown(f"**In Reservation ({len(in_reservation)})**")
                    for p in in_reservation:
                        st.success(f"✅ {p.get('nickname')} - {p.get('igg_id')}")

                with col_r2:
                    st.markdown(f"**Not in Reservation ({len(not_in_reservation)})**")

                    select_all_res = st.checkbox(
                        "Select All for Reservation", key="select_all_reservation"
                    )

                    if st.button("Add Selected to Reservations", type="primary"):
                        selected = st.session_state.get("selected_for_reservation", [])
                        if not selected:
                            st.error("No participants selected.")
                        else:
                            added = 0
                            for p in not_in_reservation:
                                if str(p.get("id")) in selected or str(p.get("id")) in [
                                    str(s) for s in selected
                                ]:
                                    try:
                                        # Create reservation for this participant
                                        db.create_reservation(
                                            user_id=p.get("user_id") or user["id"],
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

                    for p in not_in_reservation:
                        col_cb, col_info = st.columns([1, 4])
                        with col_cb:
                            checked = st.checkbox(
                                "", key=f"res_{p.get('id')}", value=select_all_res
                            )
                            if checked:
                                if "selected_for_reservation" not in st.session_state:
                                    st.session_state["selected_for_reservation"] = []
                                if (
                                    str(p.get("id"))
                                    not in st.session_state["selected_for_reservation"]
                                ):
                                    st.session_state["selected_for_reservation"].append(
                                        str(p.get("id"))
                                    )
                        with col_info:
                            st.markdown(
                                f"**{p.get('nickname')}** - {p.get('igg_id', 'N/A')}"
                            )

    # ========== Tab 3: Import Excel ==========
    with tab3:
        st.markdown("### Import Excel with Auto ID/Password Generation")

        st.markdown("""
        Upload Excel file to:
        1. Generate random passwords for new participants
        2. Create user accounts
        3. Add to participants list
        """)

        # Session selection
        session_options = ["Select Session..."] + sorted(
            set([p.get("event_name") for p in participants if p.get("event_name")])
        )
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
            help="Columns: Nickname, IGG ID (optional), Affiliation (optional), Alliance (optional)",
        )

        if uploaded_file:
            try:
                df = pd.read_excel(BytesIO(uploaded_file.read()), sheet_name=0)

                # Auto-detect columns
                nickname_col = None
                igg_col = None
                affiliation_col = None
                alliance_col = None

                for col in df.columns:
                    col_lower = str(col).lower()
                    if "nickname" in col_lower or "name" in col_lower:
                        nickname_col = col
                    elif (
                        "igg" in col_lower
                        or "commander" in col_lower
                        or "id" in col_lower
                    ):
                        igg_col = col
                    elif "affiliation" in col_lower or "guild" in col_lower:
                        affiliation_col = col
                    elif "alliance" in col_lower:
                        alliance_col = col

                st.success(f"Loaded: {uploaded_file.name} - {len(df)} rows")

                # Show column mapping
                st.markdown("### Column Mapping")
                col1, col2 = st.columns(2)
                with col1:
                    nickname_col = st.selectbox(
                        "Nickname Column",
                        list(df.columns),
                        index=list(df.columns).index(nickname_col)
                        if nickname_col
                        else 0,
                    )
                with col2:
                    igg_col = st.selectbox(
                        "IGG ID Column (Optional)",
                        ["None"] + list(df.columns),
                        index=list(df.columns).index(igg_col) + 1 if igg_col else 0,
                    )

                col3, col4 = st.columns(2)
                with col3:
                    affiliation_col = st.selectbox(
                        "Affiliation Column (Optional)",
                        ["None"] + list(df.columns),
                        index=list(df.columns).index(affiliation_col) + 1
                        if affiliation_col
                        else 0,
                    )
                with col4:
                    alliance_col = st.selectbox(
                        "Alliance Column (Optional)",
                        ["None"] + list(df.columns),
                        index=list(df.columns).index(alliance_col) + 1
                        if alliance_col
                        else 0,
                    )

                # Preview
                st.markdown("### Preview")
                preview_df = df[
                    [nickname_col] + ([igg_col] if igg_col != "None" else [])
                ].head(10)
                st.dataframe(preview_df, use_container_width=True)

                st.markdown("---")

                # Import options
                col_opt1, col_opt2 = st.columns(2)

                with col_opt1:
                    st.info(
                        f"**Import to Session**: {import_session if import_session != 'Select Session...' else 'Not selected'}"
                    )

                with col_opt2:
                    auto_generate_igg = st.checkbox(
                        "Auto-generate IGG ID if missing", value=True
                    )

                # Generate credentials preview
                if st.checkbox("Preview Generated Credentials", value=False):
                    preview_creds = []
                    for idx, row in df.head(5).iterrows():
                        nickname = str(row[nickname_col]).strip()
                        password = generate_password()
                        preview_creds.append(
                            {
                                "Nickname": nickname,
                                "Password": password,
                                "IGG ID": row.get(igg_col, "N/A")
                                if igg_col != "None"
                                else "(Auto-generated)",
                            }
                        )
                    st.dataframe(pd.DataFrame(preview_creds))

                # Import button
                if st.button(
                    "Import with Auto-generated Credentials",
                    type="primary",
                    use_container_width=True,
                ):
                    if import_session == "Select Session...":
                        st.error("Please select a session.")
                    else:
                        with st.spinner("Importing..."):
                            success_count = 0
                            password_report = []

                            for idx, row in df.iterrows():
                                try:
                                    nickname = str(row[nickname_col]).strip()
                                    if not nickname or nickname == "nan":
                                        continue

                                    igg_id = (
                                        str(row[igg_col]).strip()
                                        if igg_col != "None"
                                        and pd.notna(row.get(igg_col))
                                        else None
                                    )
                                    affiliation = (
                                        str(row[affiliation_col]).strip()
                                        if affiliation_col != "None"
                                        and pd.notna(row.get(affiliation_col))
                                        else None
                                    )
                                    alliance = (
                                        str(row[alliance_col]).strip()
                                        if alliance_col != "None"
                                        and pd.notna(row.get(alliance_col))
                                        else None
                                    )

                                    # Auto-generate IGG ID if needed
                                    if not igg_id or igg_id == "nan" or igg_id == "":
                                        igg_id = f"DG{100000 + idx:06d}"

                                    # Generate password
                                    password = generate_password()

                                    # Check if user exists
                                    existing_user = db.get_user_by_commander_number(
                                        igg_id
                                    )

                                    if existing_user:
                                        user_id = existing_user["id"]
                                        if not existing_user.get("plaintext_password"):
                                            try:
                                                db.update(
                                                    "users",
                                                    {"plaintext_password": password},
                                                    {"id": f"eq.{user_id}"},
                                                )
                                            except:
                                                pass
                                        action = "existing"
                                    else:
                                        password_hash = db.hash_password(password)
                                        user_data = {
                                            "commander_number": igg_id,
                                            "nickname": nickname,
                                            "password_hash": password_hash,
                                            "plaintext_password": password,
                                            "server": affiliation or "",
                                            "alliance": alliance or "",
                                            "is_active": True,
                                        }
                                        user_id = db.insert("users", user_data)
                                        action = "new"

                                    # Add to participants
                                    participant_data = {
                                        "nickname": nickname,
                                        "igg_id": igg_id,
                                        "affiliation": affiliation,
                                        "alliance": alliance,
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
                                            "Nickname": nickname,
                                            "IGG ID": igg_id,
                                            "Password": password,
                                            "Status": action.capitalize(),
                                        }
                                    )

                                except Exception as e:
                                    st.warning(f"Row {idx}: {e}")
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

    # ========== Tab 4: Manage Users ==========
    with tab4:
        st.markdown("### Manage User Accounts")

        st.markdown("""
        View and manage user accounts created from participant imports.
        - View plaintext passwords for distribution
        - Reset passwords if needed
        """)

        # Show users
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

            # Initialize show_password state
            if "show_passwords" not in st.session_state:
                st.session_state["show_passwords"] = {}

            # Toggle to show all passwords
            show_all = st.checkbox(
                "👁️ Show All Passwords", value=False, key="show_all_passwords"
            )

            for u in filtered_users[:50]:  # Show first 50
                user_id = str(u.get("id", ""))

                # Password visibility toggle
                show_pw = st.session_state.get(f"show_pw_{user_id}", False)
                if show_all:
                    show_pw = True

                with st.expander(
                    f"👤 {u.get('nickname', 'Unknown')} - {u.get('commander_number', 'N/A')} {'🔑' if u.get('plaintext_password') else ''}"
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
                        status = "✅ Active" if u.get("is_active") else "❌ Inactive"
                        st.markdown(f"**Status**: {status}")
                        st.markdown(
                            f"**Created**: {str(u.get('created_at', 'N/A'))[:10]}"
                        )

                        # Password display
                        if u.get("plaintext_password"):
                            col_pw, col_toggle = st.columns([3, 1])
                            with col_pw:
                                if show_pw:
                                    st.text_input(
                                        "Password",
                                        value=u.get("plaintext_password", ""),
                                        type="default",
                                        disabled=True,
                                        key=f"pw_display_{user_id}",
                                    )
                                else:
                                    st.text_input(
                                        "Password",
                                        value="••••••••••••",
                                        type="password",
                                        disabled=True,
                                        key=f"pw_hidden_{user_id}",
                                    )
                            with col_toggle:
                                if st.button(
                                    "👁️" if not show_pw else "🙈",
                                    key=f"toggle_pw_{user_id}",
                                ):
                                    st.session_state[f"show_pw_{user_id}"] = not show_pw
                                    st.rerun()
                        else:
                            st.warning("No initial password stored")

                        col_reset, col_copy = st.columns(2)
                        with col_reset:
                            if st.button(
                                "🔄 Reset Password",
                                key=f"reset_pw_{user_id}",
                                use_container_width=True,
                            ):
                                new_pw = generate_password()
                                new_hash = db.hash_password(new_pw)
                                try:
                                    db.update(
                                        "users",
                                        {
                                            "password_hash": new_hash,
                                            "plaintext_password": new_pw,
                                        },
                                        {"id": f"eq.{user_id}"},
                                    )
                                    st.success(f"Password reset! New: {new_pw}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        with col_copy:
                            if u.get("plaintext_password"):
                                # Copy button simulation (would need JavaScript in Streamlit)
                                st.info(f"Copy: {u.get('plaintext_password')}")

            # Download all credentials
            if any(u.get("plaintext_password") for u in filtered_users):
                st.markdown("---")
                all_creds = []
                for u in filtered_users:
                    if u.get("plaintext_password"):
                        all_creds.append(
                            {
                                "Nickname": u.get("nickname", ""),
                                "Commander ID": u.get("commander_number", ""),
                                "Password": u.get("plaintext_password", ""),
                                "Server": u.get("server", ""),
                                "Alliance": u.get("alliance", "") or "",
                            }
                        )
                if all_creds:
                    creds_df = pd.DataFrame(all_creds)
                    csv = creds_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download All Credentials",
                        csv,
                        "all_user_credentials.csv",
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
