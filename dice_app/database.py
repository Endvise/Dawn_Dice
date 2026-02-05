#!/usr/bin/env python3
"""
Database Management Module - Supabase REST API + Auth
"""

import streamlit as st
import bcrypt
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests

import config

# Optional Supabase SDK import (for Supabase Auth)
try:
    from supabase import create_client, Client

    _SUPABASE_SDK_AVAILABLE = True
except ImportError:
    _SUPABASE_SDK_AVAILABLE = False
    create_client = None
    Client = None

_supabase_client = None  # Will hold Supabase Client if available


def execute_query(query: str, params: tuple = (), fetch: bool | str = False) -> Any:
    """Execute query - for Supabase, this is handled by specific functions below."""
    pass


def supabase_request(
    method: str, table: str, data: Optional[Dict] = None, params: Optional[Dict] = None
) -> requests.Response:
    """Make a request to Supabase REST API."""
    url = config.get_supabase_url(table)

    if method.upper() == "GET" and params:
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        url += "?" + "&".join(query_parts)
        params = None

    headers = config.get_headers()

    if method.upper() == "GET":
        return requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        return requests.post(url, headers=headers, json=data)
    elif method.upper() == "PATCH":
        return requests.patch(url, headers=headers, json=data)
    elif method.upper() == "DELETE":
        return requests.delete(url, headers=headers)
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
        if response.headers.get("Location"):
            location = response.headers["Location"]
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
    """Initialize database - verify Supabase connection and create master account if needed."""
    try:
        response = supabase_request("GET", "users", params={"select": "id", "limit": 1})
        if response.status_code == 200:
            # Verify connection works, then initialize master account
            _init_master_account()
            return True
        elif response.status_code == 401:
            st.error("Supabase API key is invalid. Please check your secrets.")
            return False
        else:
            return True
    except Exception as e:
        st.warning(f"Database connection warning: {e}")
        return True


def _init_master_account():
    """Initialize master account from config if it doesn't exist."""
    try:
        auth_config = config.get_config()["auth"]
        master_username = auth_config["master_username"]
        master_password = auth_config["master_password"]

        if not master_username or not master_password:
            return

        # Check if master account already exists in admins table
        existing = fetch_one("admins", {"role": "eq.master"})
        if existing:
            return  # Master already exists

        # Create master account in admins table
        password_hash = hash_password(master_password)
        data = {
            "username": master_username,
            "password_hash": password_hash,
            "full_name": "Master",
            "role": "master",
        }
        insert("admins", data)
    except Exception:
        pass  # Silently fail - don't block app startup


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
    commander_number: str,
    password: str,
    nickname: Optional[str] = None,
    server: Optional[str] = None,
    alliance: Optional[str] = None,
) -> int:
    """Create user (regular user, not admin)."""
    password_hash = hash_password(password)

    data = {
        "commander_number": commander_number,
        "password_hash": password_hash,
        "nickname": nickname,
        "server": server,
        "alliance": alliance,
        "is_active": True,
    }

    return insert("users", data)


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username - now checks admins table."""
    return fetch_one("admins", {"username": f"eq.{username}"})


def get_user_by_commander_id(commander_id: str) -> Optional[Dict[str, Any]]:
    """Get user by commander ID."""
    return fetch_one("users", {"commander_number": f"eq.{commander_id}"})


def get_user_by_commander_number(commander_number: str) -> Optional[Dict[str, Any]]:
    """Get user by commander number."""
    return fetch_one("users", {"commander_number": f"eq.{commander_number}"})


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID (UUID)."""
    return fetch_one("users", {"id": f"eq.{user_id}"})


def update_user(user_id: str, **kwargs) -> bool:
    """Update user information."""
    return update("users", kwargs, {"id": f"eq.{user_id}"})


def update_user_password(user_id: str, new_password_hash: str) -> bool:
    """Update user password."""
    return update(
        "users", {"password_hash": new_password_hash}, {"id": f"eq.{user_id}"}
    )


def list_users(is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
    """List users."""
    params = {}
    if is_active is not None:
        params["is_active"] = f"eq.{is_active}"
    return fetch_all("users", params)


def delete_user(user_id: str) -> bool:
    """Delete user."""
    return delete("users", {"id": f"eq.{user_id}"})


# ==================== Admin Operations ====================


def create_admin(
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: str = "admin",
) -> int:
    """Create admin account."""
    password_hash = hash_password(password)
    data = {
        "username": username,
        "password_hash": password_hash,
        "full_name": full_name,
        "role": role,
    }
    return insert("admins", data)


def get_admin_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get admin by username."""
    return fetch_one("admins", {"username": f"eq.{username}"})


def get_admin_by_id(admin_id: str) -> Optional[Dict[str, Any]]:
    """Get admin by ID."""
    return fetch_one("admins", {"id": f"eq.{admin_id}"})


def list_admins(role: Optional[str] = None) -> List[Dict[str, Any]]:
    """List admins."""
    params = {}
    if role:
        params["role"] = f"eq.{role}"
    return fetch_all("admins", params)


def update_admin_last_login(admin_id: str) -> bool:
    """Update admin last login timestamp."""
    return update(
        "admins",
        {"last_login_at": datetime.now().isoformat()},
        {"id": f"eq.{admin_id}"},
    )


def update_admin_password(admin_id: str, new_password_hash: str) -> bool:
    """Update admin password."""
    return update(
        "admins", {"password_hash": new_password_hash}, {"id": f"eq.{admin_id}"}
    )


def delete_admin(admin_id: str) -> bool:
    """Delete admin."""
    return delete("admins", {"id": f"eq.{admin_id}"})


# ==================== Reservation Operations ====================


MAX_PARTICIPANTS = 180


def create_reservation(
    user_id: str,
    nickname: str,
    commander_number: str,
    server: str,
    notes: Optional[str] = None,
    reserved_by: Optional[str] = None,
) -> int:
    """Create reservation."""
    blacklisted = check_blacklist(commander_number)

    participants = fetch_all("participants", {"completed": "eq.1"})
    participants_count = len(participants)

    reservations = fetch_all("reservations")
    approved_reservations_count = len(reservations)

    total_count = participants_count + approved_reservations_count
    is_waitlisted = total_count >= MAX_PARTICIPANTS

    if is_waitlisted or blacklisted:
        return 0  # Cannot reserve if waitlisted or blacklisted

    data = {
        "user_id": user_id,
        "nickname": nickname,
        "commander_number": commander_number,
        "server": server,
        "notes": notes,
        "reserved_by": reserved_by,
        "reserved_at": datetime.now().isoformat(),
    }

    return insert("reservations", data)


def get_reservation_by_id(reservation_id: str) -> Optional[Dict[str, Any]]:
    """Get reservation by ID."""
    return fetch_one("reservations", {"id": f"eq.{reservation_id}"})


def list_reservations(
    user_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """List reservations."""
    params = {}
    if user_id:
        params["user_id"] = f"eq.{user_id}"
    results = fetch_all("reservations", params)
    if limit:
        results = results[:limit]
    return results


def cancel_reservation(reservation_id: int) -> bool:
    """Cancel reservation (delete)."""
    return delete("reservations", {"id": f"eq.{reservation_id}"})


def delete_reservation(reservation_id: int) -> bool:
    """Delete reservation."""
    return delete("reservations", {"id": f"eq.{reservation_id}"})


# ==================== Blacklist Operations ====================


def add_to_blacklist(
    commander_number: str,
    nickname: Optional[str] = None,
    reason: Optional[str] = None,
    blacklisted_by: Optional[str] = None,
    server: Optional[str] = None,
    expires_at: Optional[str] = None,
) -> int:
    """Add to blacklist."""
    data = {
        "commander_number": commander_number,
        "nickname": nickname,
        "server": server,
        "reason": reason,
        "blacklisted_by": blacklisted_by,
        "expires_at": expires_at,
    }
    return insert("blacklist", data)


def check_blacklist(commander_number: str) -> Optional[Dict[str, Any]]:
    """Check blacklist (local + Google Sheets)."""
    result = fetch_one("blacklist", {"commander_number": f"eq.{commander_number}"})

    if result:
        # Check if expired
        expires_at = result.get("expires_at")
        if expires_at:
            try:
                from datetime import datetime

                if datetime.fromisoformat(expires_at) < datetime.now():
                    return None  # Expired
            except Exception:
                pass
        return result

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

                commander_number_str = str(commander_number)

                for col in df.columns:
                    col_lower = str(col).lower()
                    if (
                        col_lower == "id"
                        or col_lower == "commander_number"
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
                            matched_rows = df[col_data == commander_number_str]

                            if not matched_rows.empty:
                                idx = matched_rows.index[0]
                                return {
                                    "commander_number": commander_number,
                                    "nickname": df.iloc[idx].get("nickname", ""),
                                    "reason": "Google Sheets blacklist",
                                    "source": "Google Sheets",
                                }
                        except Exception:
                            continue
    except Exception as e:
        st.warning(f"Google Sheets blacklist check failed: {e}")

    return None


def remove_from_blacklist(commander_number: str) -> bool:
    """Remove from blacklist (delete)."""
    return delete("blacklist", {"commander_number": f"eq.{commander_number}"})


def list_blacklist() -> List[Dict[str, Any]]:
    """List blacklist."""
    return fetch_all("blacklist")


# ==================== Server Operations ====================


def add_server(server_name: str, server_code: Optional[str] = None) -> int:
    """Add server."""
    return insert("servers", {"server_name": server_name, "server_code": server_code})


def list_servers(is_active: bool = True) -> List[Dict[str, Any]]:
    """List servers."""
    return fetch_all("servers", {"is_active": f"eq.{1 if is_active else 0}"})


# ==================== Alliance Operations ====================


def add_alliance(alliance_name: str, server_id: Optional[str] = None) -> int:
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
    created_by: Optional[str] = None,
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


def get_announcement_by_id(announcement_id: str) -> Optional[Dict[str, Any]]:
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
    announcement_id: str,
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


def delete_announcement(announcement_id: str) -> bool:
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


def update_participant(participant_id: str, **kwargs) -> bool:
    """Update participant."""
    return update("participants", kwargs, {"id": f"eq.{participant_id}"})


def delete_participant(participant_id: str) -> bool:
    """Delete participant."""
    return delete("participants", {"id": f"eq.{participant_id}"})


# ==================== Event Session Operations ====================


def create_session(
    session_number: int,
    session_name: str,
    session_date,
    max_participants: int,
    created_by: str,
    reservation_open_time: Optional[str] = None,
    reservation_close_time: Optional[str] = None,
):
    """Create session."""
    # date 타입을 문자열로 변환
    if hasattr(session_date, "strftime"):
        session_date_str = session_date.strftime("%Y-%m-%d")
    else:
        session_date_str = session_date

    update("event_sessions", {"is_active": False}, {"is_active": "eq.True"})

    insert(
        "event_sessions",
        {
            "session_number": session_number,
            "session_name": session_name,
            "session_date": session_date_str,
            "max_participants": max_participants,
            "reservation_open_time": reservation_open_time,
            "reservation_close_time": reservation_close_time,
            "created_by": created_by,
            "is_active": True,  # 새 세션을 활성 상태로 생성
        },
    )


def get_all_sessions():
    """Get all sessions."""
    return fetch_all("event_sessions")


def get_active_session():
    """Get active session."""
    return fetch_one("event_sessions", {"is_active": "eq.true"})


def get_next_session_number():
    """Get next session number."""
    sessions = fetch_all("event_sessions")
    if sessions:
        max_num = max(s.get("session_number", 0) for s in sessions)
        return max_num + 1
    return 1


def get_participant_count(session_id: str) -> int:
    """Get participant count for session."""
    session = fetch_one("event_sessions", {"id": f"eq.{session_id}"})
    if not session:
        return 0

    event_name = session.get("session_name", "")
    participants = fetch_all(
        "participants", {"event_name": f"eq.{event_name}", "completed": "eq.1"}
    )
    return len(participants)


def get_approved_reservation_count(session_id: str) -> int:
    """Get total reservation count for session."""
    reservations = fetch_all("reservations")
    return len(reservations)


def get_session_reservations(session_id: str):
    """Get reservations for session."""
    return fetch_all("reservations")


def get_session_participants(session_id: str):
    """Get participants for session."""
    session = fetch_one("event_sessions", {"id": f"eq.{session_id}"})
    if not session:
        return []

    event_name = session.get("session_name", "")
    return fetch_all("participants", {"event_name": f"eq.{event_name}"})


def update_session_active(session_id: str, is_active: bool):
    """Update session active status."""
    return update(
        "event_sessions",
        {"is_active": is_active},
        {"id": f"eq.{session_id}"},
    )


def delete_session(session_id: str):
    """Delete session."""
    return delete("event_sessions", {"id": f"eq.{session_id}"})


# ==================== Supabase SDK Client ====================


def get_supabase_client():
    """Get or create Supabase client instance. Returns None if SDK not available."""
    global _supabase_client
    if _supabase_client is None:
        if not _SUPABASE_SDK_AVAILABLE or not create_client:
            return None
        try:
            supabase_config = config.get_config()["supabase"]
            if supabase_config["service_role_key"]:
                _supabase_client = create_client(
                    supabase_config["url"], supabase_config["service_role_key"]
                )
        except Exception:
            pass
    return _supabase_client


# ==================== Supabase Authentication ====================


def supabase_sign_up(email: str, password: str) -> tuple[bool, str, Optional[str]]:
    """Sign up user with Supabase Auth. Returns: (success, message, user_id)"""
    client = get_supabase_client()
    if not client:
        return False, "Supabase client not initialized", None

    try:
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user:
            return True, "Sign up successful!", response.user.id
        return False, "Sign up failed", None
    except Exception as e:
        return False, f"Sign up error: {str(e)}", None


def supabase_sign_in(email: str, password: str) -> tuple[bool, str, Optional[str]]:
    """Sign in user with Supabase Auth. Returns: (success, message, access_token)"""
    client = get_supabase_client()
    if not client:
        return False, "Supabase client not initialized", None

    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if response.session:
            return True, "Login successful!", response.session.access_token
        return False, "Login failed", None
    except Exception as e:
        return False, f"Login error: {str(e)}", None


def supabase_sign_out() -> bool:
    """Sign out current user."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.auth.sign_out()
        return True
    except Exception:
        return False


def supabase_get_user(access_token: str) -> tuple[bool, Optional[Dict[str, Any]]]:
    """Get user info from access token. Returns: (success, user_data)"""
    client = get_supabase_client()
    if not client:
        return False, None

    try:
        client.auth.set_session(access_token)
        user = client.auth.get_user()
        if user:
            return True, {
                "id": user.user.id,
                "email": user.user.email,
                "created_at": user.user.created_at,
            }
        return False, None
    except Exception:
        return False, None


def supabase_verify_session(access_token: str) -> tuple[bool, Optional[str]]:
    """Verify if access token is valid. Returns: (is_valid, user_id)"""
    client = get_supabase_client()
    if not client:
        return False, None

    try:
        client.auth.set_session(access_token)
        user = client.auth.get_user()
        if user:
            return True, user.user.id
        return False, None
    except Exception:
        return False, None
