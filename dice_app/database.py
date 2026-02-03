#!/usr/bin/env python3
"""
Database Management Module - Supabase REST API
"""

import streamlit as st
import bcrypt
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests
import json

# Database configuration
DB_TYPE = st.secrets.get("DB_TYPE", "supabase")

# Supabase configuration
SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL", "https://gticuuzplbemivfturuz.supabase.co"
)
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")  # anon key

# Headers for Supabase REST API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


def get_supabase_url(table: str) -> str:
    """Get Supabase REST API URL for a table."""
    return f"{SUPABASE_URL}/rest/v1/{table}"


def execute_query(query: str, params: tuple = (), fetch: bool | str = False) -> Any:
    """Execute query - for Supabase, this is handled by specific functions below."""
    # This is kept for compatibility - actual operations use specific functions
    pass


def supabase_request(
    method: str, table: str, data: Optional[Dict] = None, params: Optional[Dict] = None
) -> requests.Response:
    """Make a request to Supabase REST API."""
    url = get_supabase_url(table)

    # Build query string for GET requests
    if method.upper() == "GET" and params:
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        url += "?" + "&".join(query_parts)
        # Use empty params for requests since we already added to URL
        params = None

    if method.upper() == "GET":
        return requests.get(url, headers=HEADERS, params=params)
    elif method.upper() == "POST":
        return requests.post(url, headers=HEADERS, json=data)
    elif method.upper() == "PATCH":
        return requests.patch(url, headers=HEADERS, json=data)
    elif method.upper() == "DELETE":
        return requests.delete(url, headers=HEADERS)
    else:
        raise ValueError(f"Unsupported method: {method}")


def fetch_one(table: str, params: Dict) -> Optional[Dict]:
    """Fetch one record from table."""
    params["limit"] = 1
    response = supabase_request("GET", table, params=params)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    return None


def fetch_all(table: str, params: Optional[Dict] = None) -> List[Dict]:
    """Fetch all records from table."""
    response = supabase_request("GET", table, params=params)
    if response.status_code == 200:
        return response.json()
    return []


def insert(table: str, data: Dict) -> int:
    """Insert a record and return the ID."""
    response = supabase_request("POST", table, data=data)
    if response.status_code in [200, 201]:
        # Return created record's id from Location header or body
        if response.headers.get("Location"):
            # Extract id from location URL
            location = response.headers["Location"]
            # Or from response body
        try:
            return response.json().get("id", 0)
        except:
            return 0
    return 0


def update(table: str, data: Dict, params: Dict) -> bool:
    """Update records matching params."""
    response = supabase_request("PATCH", table, data=data, params=params)
    return response.status_code in [200, 204]


def delete(table: str, params: Dict) -> bool:
    """Delete records matching params."""
    response = supabase_request("DELETE", table, params=params)
    return response.status_code in [200, 204]


# ==================== Database Initialization ====================


def init_database():
    """Initialize database tables - for Supabase, tables are created in Supabase dashboard."""
    # Tables should be created in Supabase dashboard
    # This function can be used to verify connection
    try:
        response = supabase_request("GET", "users", params={"select": "id", "limit": 1})
        return response.status_code == 200
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return False


# ==================== User Operations ====================


def hash_password(password: str) -> str:
    """Hash password."""
    salt = bcrypt.gensalt(rounds=st.secrets.get("PASSWORD_HASH_ROUNDS", 12))
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_user(
    username: Optional[str],
    commander_id: Optional[str],
    password: str,
    role: str = "user",
    nickname: Optional[str] = None,
    server: Optional[str] = None,
    alliance: Optional[str] = None,
) -> int:
    """Create user."""
    password_hash = hash_password(password)

    data = {
        "username": username,
        "commander_id": commander_id,
        "password_hash": password_hash,
        "role": role,
        "nickname": nickname,
        "server": server,
        "alliance": alliance,
    }

    return insert("users", data)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    return fetch_one("users", {"username": f"eq.{username}"})


def get_user_by_commander_id(commander_id: str) -> Optional[Dict[str, Any]]:
    """Get user by commander ID."""
    return fetch_one("users", {"commander_id": f"eq.{commander_id}"})


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    return fetch_one("users", {"id": f"eq.{user_id}"})


def update_user(user_id: int, **kwargs) -> bool:
    """Update user information."""
    return update("users", kwargs, {"id": f"eq.{user_id}"})


def list_users(
    role: Optional[str] = None, is_active: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """List users."""
    params = {}
    if role:
        params["role"] = f"eq.{role}"
    if is_active is not None:
        params["is_active"] = f"eq.{1 if is_active else 0}"
    return fetch_all("users", params)


def delete_user(user_id: int) -> bool:
    """Delete user."""
    return delete("users", {"id": f"eq.{user_id}"})


# ==================== Reservation Operations ====================


MAX_PARTICIPANTS = 180


def create_reservation(
    user_id: int,
    nickname: str,
    commander_id: str,
    server: str,
    alliance: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """Create reservation."""
    blacklisted = check_blacklist(commander_id)

    # Check capacity
    participants = fetch_all("participants", {"completed": f"eq.1"})
    participants_count = len(participants)

    reservations = fetch_all("reservations", {"status": f"eq.approved"})
    approved_reservations_count = len(reservations)

    total_count = participants_count + approved_reservations_count
    is_waitlisted = total_count >= MAX_PARTICIPANTS

    waitlist_order = None
    waitlist_position = None
    status = "pending"

    if is_waitlisted:
        waitlist_reservations = fetch_all(
            "reservations", {"waitlist_order": "not.is.null"}
        )
        waitlist_count = len(waitlist_reservations)
        waitlist_order = waitlist_count + 1
        waitlist_position = waitlist_order
        status = "waitlisted"

    data = {
        "user_id": user_id,
        "nickname": nickname,
        "commander_id": commander_id,
        "server": server,
        "alliance": alliance,
        "notes": notes,
        "is_blacklisted": 1 if blacklisted else 0,
        "blacklist_reason": blacklisted.get("reason") if blacklisted else None,
        "status": status,
        "waitlist_order": waitlist_order,
        "waitlist_position": waitlist_position,
    }

    return insert("reservations", data)


def get_reservation_by_id(reservation_id: int) -> Optional[Dict[str, Any]]:
    """Get reservation by ID."""
    return fetch_one("reservations", {"id": f"eq.{reservation_id}"})


def list_reservations(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    is_blacklisted: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """List reservations."""
    params = {}
    if status:
        params["status"] = f"eq.{status}"
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    if is_blacklisted is not None:
        params["is_blacklisted"] = f"eq.{1 if is_blacklisted else 0}"
    return fetch_all("reservations", params)


def update_reservation_status(
    reservation_id: int, status: str, approved_by: int
) -> bool:
    """Update reservation status."""
    now = datetime.now().isoformat()
    return update(
        "reservations",
        {"status": status, "approved_at": now, "approved_by": approved_by},
        {"id": f"eq.{reservation_id}"},
    )


def cancel_reservation(reservation_id: int) -> bool:
    """Cancel reservation."""
    return update(
        "reservations", {"status": "cancelled"}, {"id": f"eq.{reservation_id}"}
    )


def delete_reservation(reservation_id: int) -> bool:
    """Delete reservation."""
    return delete("reservations", {"id": f"eq.{reservation_id}"})


# ==================== Blacklist Operations ====================


def add_to_blacklist(
    commander_id: str,
    nickname: Optional[str] = None,
    reason: Optional[str] = None,
    added_by: Optional[int] = None,
) -> int:
    """Add to blacklist."""
    data = {
        "commander_id": commander_id,
        "nickname": nickname,
        "reason": reason,
        "added_by": added_by,
    }
    return insert("blacklist", data)


def check_blacklist(commander_id: str) -> Optional[Dict[str, Any]]:
    """Check blacklist (local + Google Sheets)."""
    result = fetch_one(
        "blacklist", {"commander_id": f"eq.{commander_id}", "is_active": "eq.1"}
    )

    if result:
        return result

    # Check Google Sheets
    try:
        import requests as req

        sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
        if sheet_url:
            response = req.get(sheet_url)
            if response.status_code == 200:
                import pandas as pd
                from io import StringIO

                try:
                    df = pd.read_csv(StringIO(response.text), on_bad_lines="skip")
                except Exception:
                    try:
                        df = pd.read_csv(
                            StringIO(response.text),
                            on_bad_lines="skip",
                            encoding="utf-8-sig",
                        )
                    except Exception:
                        df = pd.DataFrame()

                if df.empty:
                    return None

                commander_id_str = str(commander_id)

                for col in df.columns:
                    col_lower = str(col).lower()
                    if (
                        col_lower == "id"
                        or col_lower == "commander_id"
                        or col_lower == "사령관번호"
                        or (
                            col_lower.startswith("igg")
                            and not any(
                                kw in col_lower
                                for kw in ["nickname", "name", "alliance", "소속"]
                            )
                        )
                    ):
                        try:
                            col_data = df[col].astype(str).str.strip()
                            matched_rows = df[col_data == commander_id_str]

                            if not matched_rows.empty:
                                idx = matched_rows.index[0]
                                return {
                                    "commander_id": commander_id,
                                    "nickname": df.iloc[idx].get("nickname", ""),
                                    "reason": "Google Sheets blacklist",
                                    "is_active": 1,
                                    "source": "Google Sheets",
                                }
                        except Exception:
                            continue
    except Exception as e:
        st.warning(f"Google Sheets blacklist check failed: {e}")

    return None


def remove_from_blacklist(commander_id: str) -> bool:
    """Remove from blacklist."""
    return update("blacklist", {"is_active": 0}, {"commander_id": f"eq.{commander_id}"})


def list_blacklist(is_active: bool = True) -> List[Dict[str, Any]]:
    """List blacklist."""
    return fetch_all("blacklist", {"is_active": f"eq.{1 if is_active else 0}"})


# ==================== Server Operations ====================


def add_server(server_name: str, server_code: Optional[str] = None) -> int:
    """Add server."""
    return insert("servers", {"server_name": server_name, "server_code": server_code})


def list_servers(is_active: bool = True) -> List[Dict[str, Any]]:
    """List servers."""
    return fetch_all("servers", {"is_active": f"eq.{1 if is_active else 0}"})


# ==================== Alliance Operations ====================


def add_alliance(alliance_name: str, server_id: Optional[int] = None) -> int:
    """Add alliance."""
    return insert("alliances", {"alliance_name": alliance_name, "server_id": server_id})


def list_alliances(is_active: bool = True) -> List[Dict[str, Any]]:
    """List alliances."""
    return fetch_all("alliances", {"is_active": f"eq.{1 if is_active else 0}"})


# ==================== Announcement Operations ====================


def create_announcement(
    title: str,
    content: str,
    category: str = "notice",
    is_pinned: bool = False,
    created_by: Optional[int] = None,
) -> int:
    """Create announcement."""
    return insert(
        "announcements",
        {
            "title": title,
            "content": content,
            "category": category,
            "is_pinned": 1 if is_pinned else 0,
            "created_by": created_by,
        },
    )


def get_announcement_by_id(announcement_id: int) -> Optional[Dict[str, Any]]:
    """Get announcement by ID."""
    return fetch_one("announcements", {"id": f"eq.{announcement_id}"})


def list_announcements(
    is_active: bool = True, category: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """List announcements."""
    params = {"is_active": f"eq.{1 if is_active else 0}"}
    if category:
        params["category"] = f"eq.{category}"
    results = fetch_all("announcements", params)
    if limit:
        results = results[:limit]
    return results


def update_announcement(
    announcement_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    is_active: Optional[bool] = None,
) -> bool:
    """Update announcement."""
    data = {}
    if title is not None:
        data["title"] = title
    if content is not None:
        data["content"] = content
    if category is not None:
        data["category"] = category
    if is_pinned is not None:
        data["is_pinned"] = 1 if is_pinned else 0
    if is_active is not None:
        data["is_active"] = 1 if is_active else 0

    if data:
        data["updated_at"] = datetime.now().isoformat()
        return update("announcements", data, {"id": f"eq.{announcement_id}"})
    return False


def delete_announcement(announcement_id: int) -> bool:
    """Delete announcement."""
    return delete("announcements", {"id": f"eq.{announcement_id}"})


# ==================== Participant Operations ====================


def add_participant(data: Dict[str, Any]) -> int:
    """Add participant."""
    participant_data = {
        "number": data.get("number"),
        "nickname": data.get("nickname"),
        "affiliation": data.get("affiliation"),
        "igg_id": data.get("igg_id"),
        "alliance": data.get("alliance"),
        "wait_confirmed": data.get("wait_confirmed", 0),
        "confirmed": data.get("confirmed", 0),
        "notes": data.get("notes"),
        "completed": data.get("completed", 0),
        "participation_record": data.get("participation_record"),
        "event_name": data.get("event_name"),
    }
    return insert("participants", participant_data)


def list_participants(event_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """List participants."""
    if event_name:
        return fetch_all("participants", {"event_name": f"eq.{event_name}"})
    return fetch_all("participants")


def update_participant(participant_id: int, **kwargs) -> bool:
    """Update participant."""
    return update("participants", kwargs, {"id": f"eq.{participant_id}"})


def delete_participant(participant_id: int) -> bool:
    """Delete participant."""
    return delete("participants", {"id": f"eq.{participant_id}"})


# ==================== Event Session Operations ====================


def create_session(
    session_number: int,
    session_name: str,
    session_date,
    max_participants: int,
    created_by: int,
    reservation_open_time: Optional[str] = None,
    reservation_close_time: Optional[str] = None,
):
    """Create session."""
    # Deactivate all existing sessions
    update("event_sessions", {"is_active": 0}, {"is_active": "eq.1"})

    insert(
        "event_sessions",
        {
            "session_number": session_number,
            "session_name": session_name,
            "session_date": session_date,
            "max_participants": max_participants,
            "reservation_open_time": reservation_open_time,
            "reservation_close_time": reservation_close_time,
            "created_by": created_by,
        },
    )


def get_all_sessions():
    """Get all sessions."""
    return fetch_all("event_sessions")


def get_active_session():
    """Get active session."""
    return fetch_one("event_sessions", {"is_active": "eq.1"})


def get_next_session_number():
    """Get next session number."""
    sessions = fetch_all("event_sessions")
    if sessions:
        max_num = max(s.get("session_number", 0) for s in sessions)
        return max_num + 1
    return 1


def get_participant_count(session_id: int) -> int:
    """Get participant count for session."""
    session = fetch_one("event_sessions", {"id": f"eq.{session_id}"})
    if not session:
        return 0

    event_name = session.get("session_name", "")
    participants = fetch_all(
        "participants", {"event_name": f"eq.{event_name}", "completed": "eq.1"}
    )
    return len(participants)


def get_approved_reservation_count(session_id: int) -> int:
    """Get approved reservation count for session."""
    reservations = fetch_all("reservations", {"status": "eq.approved"})
    return len(reservations)


def get_session_reservations(session_id: int):
    """Get reservations for session."""
    return fetch_all("reservations")


def get_session_participants(session_id: int):
    """Get participants for session."""
    session = fetch_one("event_sessions", {"id": f"eq.{session_id}"})
    if not session:
        return []

    event_name = session.get("session_name", "")
    return fetch_all("participants", {"event_name": f"eq.{event_name}"})


def update_session_active(session_id: int, is_active: bool):
    """Update session active status."""
    return update(
        "event_sessions",
        {"is_active": 1 if is_active else 0},
        {"id": f"eq.{session_id}"},
    )


def delete_session(session_id: int):
    """Delete session."""
    return delete("event_sessions", {"id": f"eq.{session_id}"})
