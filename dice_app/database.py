#!/usr/bin/env python3
"""
Database Management Module - Supports SQLite and PostgreSQL (Supabase)
"""

import sqlite3
import psycopg2
from psycopg2 import sql
import streamlit as st
import bcrypt
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading

# Database configuration
DB_TYPE = st.secrets.get("DB_TYPE", "sqlite")

# SQLite configuration
DB_PATH = Path(st.secrets.get("DB_PATH", "data/dice_app.db"))

# PostgreSQL configuration (Supabase)
DB_CONNECTION_STRING = st.secrets.get("DB_CONNECTION_STRING", "")

# Thread-local storage for connections
_local = threading.local()


def get_connection():
    """Get database connection (thread-safe)."""
    if DB_TYPE == "postgresql":
        return get_postgres_connection()
    else:
        return get_sqlite_connection()


def get_sqlite_connection() -> sqlite3.Connection:
    """Get SQLite database connection (thread-safe)."""
    if not hasattr(_local, "connection") or _local.connection is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        _local.connection = conn
    return _local.connection


def get_postgres_connection():
    """Get PostgreSQL database connection (thread-safe)."""
    if not hasattr(_local, "connection") or _local.connection is None:
        conn = psycopg2.connect(DB_CONNECTION_STRING)
        conn.autocommit = False
        _local.connection = conn
    return _local.connection


def execute_query(query: str, params: tuple = (), fetch: bool | str = False) -> Any:
    """Execute SQL query."""
    conn = get_connection()

    if DB_TYPE == "postgresql":
        # Convert SQLite placeholders to PostgreSQL
        pg_query = query.replace("?", "%s")
        return execute_postgres_query(conn, pg_query, params, fetch)
    else:
        return execute_sqlite_query(conn, query, params, fetch)


def execute_sqlite_query(conn, query: str, params: tuple, fetch: bool | str) -> Any:
    """Execute SQLite query."""
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)

        if fetch:
            if fetch == "one":
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
            elif fetch == "all":
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
            else:
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []

        conn.commit()
        return cursor

    except sqlite3.OperationalError as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        raise
    except Exception as e:
        conn.rollback()
        raise


def execute_postgres_query(conn, query: str, params: tuple, fetch: bool | str) -> Any:
    """Execute PostgreSQL query."""
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)

        if fetch:
            if fetch == "one":
                result = cursor.fetchone()
                if result:
                    # Convert to dict with column names
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
                return None
            elif fetch == "all":
                results = cursor.fetchall()
                if results:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                return []
            else:
                results = cursor.fetchall()
                if results:
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in results]
                return []

        conn.commit()
        return cursor

    except psycopg2.OperationalError as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        raise
    except Exception as e:
        conn.rollback()
        raise


def init_database():
    """Initialize database tables."""
    # Users 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            commander_id TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            nickname TEXT,
            server TEXT,
            alliance TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            failed_attempts INTEGER DEFAULT 0
        )
    """)

    # Reservations 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nickname TEXT NOT NULL,
            commander_id TEXT NOT NULL,
            server TEXT NOT NULL,
            alliance TEXT,
            status TEXT DEFAULT 'pending',
            is_blacklisted INTEGER DEFAULT 0,
            blacklist_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            notes TEXT,
            waitlist_order INTEGER,
            waitlist_position INTEGER
        )
    """)

    # Blacklist 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commander_id TEXT UNIQUE NOT NULL,
            nickname TEXT,
            reason TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_by INTEGER,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Servers 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT UNIQUE NOT NULL,
            server_code TEXT UNIQUE,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Alliances 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS alliances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alliance_name TEXT UNIQUE NOT NULL,
            server_id INTEGER,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Participants 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER,
            nickname TEXT,
            affiliation TEXT,
            igg_id TEXT,
            alliance TEXT,
            wait_confirmed INTEGER DEFAULT 0,
            confirmed INTEGER DEFAULT 0,
            notes TEXT,
            completed INTEGER DEFAULT 0,
            participation_record TEXT,
            event_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Announcements 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'notice',
            is_pinned INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)

    # Event Sessions 테이블
    execute_query("""
        CREATE TABLE IF NOT EXISTS event_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_number INTEGER,
            session_name TEXT,
            session_date DATE,
            max_participants INTEGER DEFAULT 180,
            reservation_open_time DATETIME,
            reservation_close_time DATETIME,
            is_active INTEGER DEFAULT 1,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 인덱스 생성
    create_indexes()


def create_indexes():
    """Create database indexes."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_commander_id ON users(commander_id)",
        "CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status)",
        "CREATE INDEX IF NOT EXISTS idx_blacklist_commander_id ON blacklist(commander_id)",
        "CREATE INDEX IF NOT EXISTS idx_participants_igg_id ON participants(igg_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_sessions_is_active ON event_sessions(is_active)",
    ]

    for idx_query in indexes:
        try:
            execute_query(idx_query)
        except:
            pass


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

    execute_query(
        """
        INSERT INTO users (username, commander_id, password_hash, role, nickname, server, alliance)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (username, commander_id, password_hash, role, nickname, server, alliance),
    )

    return get_last_insert_id()


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    result = execute_query(
        "SELECT * FROM users WHERE username = ?", (username,), fetch="one"
    )
    return result


def get_user_by_commander_id(commander_id: str) -> Optional[Dict[str, Any]]:
    """Get user by commander ID."""
    result = execute_query(
        "SELECT * FROM users WHERE commander_id = ?", (commander_id,), fetch="one"
    )
    return result


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    result = execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch="one")
    return result


def update_user(user_id: int, **kwargs) -> bool:
    """Update user information."""
    fields = []
    values = []

    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"

    execute_query(query, tuple(values))
    return True


def list_users(
    role: Optional[str] = None, is_active: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """List users."""
    conditions = []
    params = []

    if role:
        conditions.append("role = ?")
        params.append(role)

    if is_active is not None:
        conditions.append("is_active = ?")
        params.append(1 if is_active else 0)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM users{where_clause} ORDER BY created_at DESC"

    results = execute_query(query, tuple(params), fetch="all")
    return results if results else []


def delete_user(user_id: int) -> bool:
    """Delete user."""
    execute_query("DELETE FROM users WHERE id = ?", (user_id,))
    return True


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

    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    )
    participants_count = result.get("count", 0) if result else 0

    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    approved_reservations_count = result.get("count", 0) if result else 0

    total_count = participants_count + approved_reservations_count
    is_waitlisted = total_count >= MAX_PARTICIPANTS

    waitlist_order = None
    waitlist_position = None
    status = "pending"

    if is_waitlisted:
        result = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE waitlist_order IS NOT NULL",
            fetch="one",
        )
        waitlist_count = result.get("count", 0) if result else 0

        waitlist_order = waitlist_count + 1
        waitlist_position = waitlist_order
        status = "waitlisted"

    execute_query(
        """
        INSERT INTO reservations (
            user_id, nickname, commander_id, server, alliance, notes,
            is_blacklisted, blacklist_reason, status, waitlist_order, waitlist_position
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            user_id,
            nickname,
            commander_id,
            server,
            alliance,
            notes,
            1 if blacklisted else 0,
            blacklisted.get("reason") if blacklisted else None,
            status,
            waitlist_order,
            waitlist_position,
        ),
    )

    return get_last_insert_id()


def get_reservation_by_id(reservation_id: int) -> Optional[Dict[str, Any]]:
    """Get reservation by ID."""
    result = execute_query(
        "SELECT * FROM reservations WHERE id = ?", (reservation_id,), fetch="one"
    )
    return result


def list_reservations(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    is_blacklisted: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """List reservations."""
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)

    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)

    if is_blacklisted is not None:
        conditions.append("is_blacklisted = ?")
        params.append(1 if is_blacklisted else 0)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"""
        SELECT r.*, u.nickname as user_nickname, u.role as user_role
        FROM reservations r
        LEFT JOIN users u ON r.user_id = u.id
        {where_clause}
        ORDER BY r.created_at DESC
    """

    results = execute_query(query, tuple(params), fetch="all")
    return results if results else []


def update_reservation_status(
    reservation_id: int, status: str, approved_by: int
) -> bool:
    """Update reservation status."""
    now = datetime.now()
    execute_query(
        """
        UPDATE reservations
        SET status = ?, approved_at = ?, approved_by = ?
        WHERE id = ?
    """,
        (status, now, approved_by, reservation_id),
    )
    return True


def cancel_reservation(reservation_id: int) -> bool:
    """Cancel reservation."""
    execute_query(
        "UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,)
    )
    return True


def delete_reservation(reservation_id: int) -> bool:
    """Delete reservation."""
    execute_query("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    return True


# ==================== Blacklist Operations ====================


def add_to_blacklist(
    commander_id: str,
    nickname: Optional[str] = None,
    reason: Optional[str] = None,
    added_by: Optional[int] = None,
) -> int:
    """Add to blacklist."""
    execute_query(
        """
        INSERT INTO blacklist (commander_id, nickname, reason, added_by)
        VALUES (?, ?, ?, ?)
    """,
        (commander_id, nickname, reason, added_by),
    )

    execute_query(
        """
        UPDATE reservations
        SET is_blacklisted = 1, blacklist_reason = ?
        WHERE commander_id = ?
    """,
        (reason, commander_id),
    )

    return get_last_insert_id()


def check_blacklist(commander_id: str) -> Optional[Dict[str, Any]]:
    """Check blacklist (local + Google Sheets)."""
    result = execute_query(
        "SELECT * FROM blacklist WHERE commander_id = ? AND is_active = 1",
        (commander_id,),
        fetch="one",
    )

    if result:
        return result

    # Check Google Sheets
    try:
        import requests

        sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
        if sheet_url:
            response = requests.get(sheet_url)
            if response.status_code == 200:
                import pandas as pd
                from io import StringIO

                try:
                    df = pd.read_csv(
                        StringIO(response.text),
                        on_bad_lines="skip",
                        encoding="utf-8",
                    )
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

                for col in df.columns:
                    if any(
                        keyword in str(col).lower()
                        for keyword in ["igg", "commander", "사령관"]
                    ):
                        try:
                            if (
                                df[col]
                                .astype(str)
                                .str.contains(commander_id_str, na=False)
                                .any()
                            ):
                                matched_rows = df[
                                    df[col]
                                    .astype(str)
                                    .str.contains(commander_id_str, na=False)
                                ]
                                idx = matched_rows.index[0]
                                return {
                                    "commander_id": commander_id,
                                    "nickname": df.iloc[idx].get("nickname", ""),
                                    "reason": "Google Sheets blacklist (partial match)",
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
    execute_query(
        "UPDATE blacklist SET is_active = 0 WHERE commander_id = ?", (commander_id,)
    )
    return True


def list_blacklist(is_active: bool = True) -> List[Dict[str, Any]]:
    """List blacklist."""
    results = execute_query(
        "SELECT * FROM blacklist WHERE is_active = ? ORDER BY added_at DESC",
        (1 if is_active else 0,),
        fetch="all",
    )
    return results if results else []


# ==================== Server Operations ====================


def add_server(server_name: str, server_code: Optional[str] = None) -> int:
    """Add server."""
    execute_query(
        "INSERT INTO servers (server_name, server_code) VALUES (?, ?)",
        (server_name, server_code),
    )

    return get_last_insert_id()


def list_servers(is_active: bool = True) -> List[Dict[str, Any]]:
    """List servers."""
    results = execute_query(
        "SELECT * FROM servers WHERE is_active = ? ORDER BY server_name",
        (1 if is_active else 0,),
        fetch="all",
    )
    return results if results else []


# ==================== Alliance Operations ====================


def add_alliance(alliance_name: str, server_id: Optional[int] = None) -> int:
    """Add alliance."""
    execute_query(
        "INSERT INTO alliances (alliance_name, server_id) VALUES (?, ?)",
        (alliance_name, server_id),
    )

    return get_last_insert_id()


def list_alliances(is_active: bool = True) -> List[Dict[str, Any]]:
    """List alliances."""
    results = execute_query(
        "SELECT a.*, s.server_name FROM alliances a LEFT JOIN servers s ON a.server_id = s.id WHERE a.is_active = ? ORDER BY a.alliance_name",
        (1 if is_active else 0,),
        fetch="all",
    )
    return results if results else []


# ==================== Announcement Operations ====================


def create_announcement(
    title: str,
    content: str,
    category: str = "notice",
    is_pinned: bool = False,
    created_by: Optional[int] = None,
) -> int:
    """Create announcement."""
    execute_query(
        """
        INSERT INTO announcements (title, content, category, is_pinned, created_by)
        VALUES (?, ?, ?, ?, ?)
    """,
        (title, content, category, 1 if is_pinned else 0, created_by),
    )

    return get_last_insert_id()


def get_announcement_by_id(announcement_id: int) -> Optional[Dict[str, Any]]:
    """Get announcement by ID."""
    result = execute_query(
        """
        SELECT a.*, u.nickname as author_name
        FROM announcements a
        LEFT JOIN users u ON a.created_by = u.id
        WHERE a.id = ?
    """,
        (announcement_id,),
        fetch="one",
    )
    return result


def list_announcements(
    is_active: bool = True, category: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """List announcements."""
    conditions = ["a.is_active = ?"]
    params: List[Any] = [1 if is_active else 0]

    if category:
        conditions.append("a.category = ?")
        params.append(category)

    where_clause = " WHERE " + " AND ".join(conditions)
    order_clause = " ORDER BY a.is_pinned DESC, a.created_at DESC"

    query = f"""
        SELECT a.*, u.nickname as author_name
        FROM announcements a
        LEFT JOIN users u ON a.created_by = u.id
        {where_clause}{order_clause}
    """

    if limit:
        query += f" LIMIT {limit}"

    results = execute_query(query, tuple(params), fetch="all")
    return results if results else []


def update_announcement(
    announcement_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    is_active: Optional[bool] = None,
) -> bool:
    """Update announcement."""
    fields = []
    values = []

    if title is not None:
        fields.append("title = ?")
        values.append(title)

    if content is not None:
        fields.append("content = ?")
        values.append(content)

    if category is not None:
        fields.append("category = ?")
        values.append(category)

    if is_pinned is not None:
        fields.append("is_pinned = ?")
        values.append(1 if is_pinned else 0)

    if is_active is not None:
        fields.append("is_active = ?")
        values.append(1 if is_active else 0)

    if fields:
        fields.append("updated_at = ?")
        values.append(datetime.now())

    if not fields:
        return False

    values.append(announcement_id)
    query = f"UPDATE announcements SET {', '.join(fields)} WHERE id = ?"

    execute_query(query, tuple(values))
    return True


def delete_announcement(announcement_id: int) -> bool:
    """Delete announcement."""
    execute_query("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    return True


# ==================== Participant Operations ====================


def add_participant(data: Dict[str, Any]) -> int:
    """Add participant."""
    execute_query(
        """
        INSERT INTO participants (
            number, nickname, affiliation, igg_id, alliance,
            wait_confirmed, confirmed, notes, completed, participation_record, event_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("number"),
            data.get("nickname"),
            data.get("affiliation"),
            data.get("igg_id"),
            data.get("alliance"),
            data.get("wait_confirmed", 0),
            data.get("confirmed", 0),
            data.get("notes"),
            data.get("completed", 0),
            data.get("participation_record"),
            data.get("event_name"),
        ),
    )

    return get_last_insert_id()


def list_participants(event_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """List participants."""
    if event_name:
        results = execute_query(
            "SELECT * FROM participants WHERE event_name = ? ORDER BY number",
            (event_name,),
            fetch="all",
        )
    else:
        results = execute_query(
            "SELECT * FROM participants ORDER BY event_name, number", fetch="all"
        )
    return results if results else []


def update_participant(participant_id: int, **kwargs) -> bool:
    """Update participant."""
    fields = []
    values = []

    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(participant_id)
    query = f"UPDATE participants SET {', '.join(fields)} WHERE id = ?"

    execute_query(query, tuple(values))
    return True


def delete_participant(participant_id: int) -> bool:
    """Delete participant."""
    execute_query("DELETE FROM participants WHERE id = ?", (participant_id,))
    return True


# ==================== Event Session Operations ====================


def get_last_insert_id():
    """Get last inserted ID (works with both SQLite and PostgreSQL)."""
    if DB_TYPE == "postgresql":
        result = execute_query("SELECT lastval() as lastval", fetch="one")
        return result["lastval"] if result else 0
    else:
        result = execute_query("SELECT last_insert_rowid() as id", fetch="one")
        return result["id"] if result else 0


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
    execute_query("UPDATE event_sessions SET is_active = 0")

    execute_query(
        """
        INSERT INTO event_sessions (session_number, session_name, session_date, max_participants, reservation_open_time, reservation_close_time, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            session_number,
            session_name,
            session_date,
            max_participants,
            reservation_open_time,
            reservation_close_time,
            created_by,
        ),
    )


def get_all_sessions():
    """Get all sessions."""
    results = execute_query(
        """
        SELECT s.*, u.nickname as creator_name
        FROM event_sessions s
        LEFT JOIN users u ON s.created_by = u.id
        ORDER BY s.session_number DESC
    """,
        fetch="all",
    )
    return results if results else []


def get_active_session():
    """Get active session."""
    result = execute_query(
        """
        SELECT s.*, u.nickname as creator_name
        FROM event_sessions s
        LEFT JOIN users u ON s.created_by = u.id
        WHERE s.is_active = 1
        LIMIT 1
    """,
        fetch="one",
    )
    return result


def get_next_session_number():
    """Get next session number."""
    result = execute_query(
        "SELECT MAX(session_number) as max_number FROM event_sessions", fetch="one"
    )
    return (result.get("max_number", 0) if result else 0) + 1


def get_participant_count(session_id: int) -> int:
    """Get participant count for session."""
    session = execute_query(
        "SELECT session_name FROM event_sessions WHERE id = ?",
        (session_id,),
        fetch="one",
    )

    if not session:
        return 0

    event_name = session.get("session_name", "")
    result = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE event_name = ? AND completed = 1",
        (event_name,),
        fetch="one",
    )
    return result.get("count", 0) if result else 0


def get_approved_reservation_count(session_id: int) -> int:
    """Get approved reservation count for session."""
    result = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    )
    return result.get("count", 0) if result else 0


def get_session_reservations(session_id: int):
    """Get reservations for session."""
    return list_reservations()


def get_session_participants(session_id: int):
    """Get participants for session."""
    session = execute_query(
        "SELECT session_name FROM event_sessions WHERE id = ?",
        (session_id,),
        fetch="one",
    )

    if not session:
        return []

    event_name = session.get("session_name", "")
    results = execute_query(
        "SELECT * FROM participants WHERE event_name = ? ORDER BY number",
        (event_name,),
        fetch="all",
    )
    return results if results else []


def update_session_active(session_id: int, is_active: bool):
    """Update session active status."""
    execute_query(
        "UPDATE event_sessions SET is_active = ? WHERE id = ?",
        (1 if is_active else 0, session_id),
    )


def delete_session(session_id: int):
    """Delete session."""
    execute_query("DELETE FROM event_sessions WHERE id = ?", (session_id,))


# ==================== Initialization ====================


def initialize_master_account():
    """Initialize master account."""
    master_username = st.secrets.get("MASTER_USERNAME", "DaWnntt0623")
    master_password = st.secrets.get("MASTER_PASSWORD", "4425endvise9897!")

    existing = get_user_by_username(master_username)
    if not existing:
        create_user(
            username=master_username,
            commander_id=None,
            password=master_password,
            role="master",
            nickname="Master Admin",
        )
        st.success(f"Master account created: {master_username}")


def init_app():
    """Initialize app."""
    init_database()
    initialize_master_account()

    default_servers = [
        "#095 woLF",
        "#708 아시아",
    ]
    for server_name in default_servers:
        try:
            add_server(server_name, server_name.split()[0])
        except:
            pass
