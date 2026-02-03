#!/usr/bin/env python3
"""
데이터베이스 관리 모듈
"""

import sqlite3
import streamlit as st
import bcrypt
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# 데이터베이스 경로
DB_PATH = Path(st.secrets.get("DB_PATH", "data/dice_app.db"))


@st.cache_resource
def get_connection() -> sqlite3.Connection:
    """데이터베이스 연결을 캐시하여 반환합니다."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn


def execute_query(query: str, params: tuple = (), fetch: bool | str = False) -> Any:
    """SQL 쿼리를 실행합니다."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query, params)
        if fetch:
            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                result = cursor.fetchall()
            conn.commit()
            return result
        else:
            conn.commit()
            return None
    except sqlite3.OperationalError as e:
        conn.rollback()
        st.error(f"데이터베이스 오류: {e}")
        st.error(f"쿼리: {query[:100]}...")
        raise e
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        # 커서를 닫지 않음 (연결이 캐시되므로)
        pass


def init_database():
    """데이터베이스 테이블을 초기화합니다."""
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
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id)
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
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (added_by) REFERENCES users(id)
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
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (server_id) REFERENCES servers(id)
        )
    """)

    # Participants 테이블 (기존 참여자 목록)
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

    # Announcements 테이블 (공지사항)
    execute_query("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT '공지',
            is_pinned INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # Event Sessions 테이블 (이벤트 회차 관리)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # 인덱스 생성
    create_indexes()


def create_indexes():
    """데이터베이스 인덱스를 생성합니다."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_commander_id ON users(commander_id)",
        "CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status)",
        "CREATE INDEX IF NOT EXISTS idx_blacklist_commander_id ON blacklist(commander_id)",
        "CREATE INDEX IF NOT EXISTS idx_participants_igg_id ON participants(igg_id)",
        "CREATE INDEX IF NOT EXISTS idx_event_sessions_is_active ON event_sessions(is_active)",
    ]

    for idx_query in indexes:
        execute_query(idx_query)


def hash_password(password: str) -> str:
    """비밀번호를 해시화합니다."""
    salt = bcrypt.gensalt(rounds=st.secrets.get("PASSWORD_HASH_ROUNDS", 12))
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호를 검증합니다."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# ==================== User Operations ====================


def create_user(
    username: Optional[str],
    commander_id: Optional[str],
    password: str,
    role: str = "user",
    nickname: Optional[str] = None,
    server: Optional[str] = None,
    alliance: Optional[str] = None,
) -> int:
    """사용자를 생성합니다."""
    password_hash = hash_password(password)

    result = execute_query(
        """
        INSERT INTO users (username, commander_id, password_hash, role, nickname, server, alliance)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (username, commander_id, password_hash, role, nickname, server, alliance),
    )

    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """사용자명으로 사용자를 조회합니다."""
    result = execute_query(
        "SELECT * FROM users WHERE username = ?", (username,), fetch="one"
    )
    return dict(result) if result else None


def get_user_by_commander_id(commander_id: str) -> Optional[Dict[str, Any]]:
    """사령관번호로 사용자를 조회합니다."""
    result = execute_query(
        "SELECT * FROM users WHERE commander_id = ?", (commander_id,), fetch="one"
    )
    return dict(result) if result else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """ID로 사용자를 조회합니다."""
    result = execute_query("SELECT * FROM users WHERE id = ?", (user_id,), fetch="one")
    return dict(result) if result else None


def update_user(user_id: int, **kwargs) -> bool:
    """사용자 정보를 업데이트합니다."""
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
    """사용자 목록을 조회합니다."""
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
    return [dict(row) for row in results]


def delete_user(user_id: int) -> bool:
    """사용자를 삭제합니다."""
    execute_query("DELETE FROM users WHERE id = ?", (user_id,))
    return True


# ==================== Reservation Operations ====================

MAX_PARTICIPANTS = 180  # 최대 참여자 수


def create_reservation(
    user_id: int,
    nickname: str,
    commander_id: str,
    server: str,
    alliance: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """예약을 생성합니다."""
    # 블랙리스트 체크
    blacklisted = check_blacklist(commander_id)

    # 기존 참여자 수 체크
    participants_count = execute_query(
        "SELECT COUNT(*) as count FROM participants WHERE completed = 1", fetch="one"
    ).get("count", 0)

    # 승인된 예약자 수 체크
    approved_reservations_count = execute_query(
        "SELECT COUNT(*) as count FROM reservations WHERE status = 'approved'",
        fetch="one",
    ).get("count", 0)

    # 전체 참여자 수
    total_count = participants_count + approved_reservations_count

    # 대기자 여부 및 순번 결정
    is_waitlisted = total_count >= MAX_PARTICIPANTS

    waitlist_order = None
    waitlist_position = None
    status = "pending"

    if is_waitlisted:
        # 대기자 순번 계산
        waitlist_count = execute_query(
            "SELECT COUNT(*) as count FROM reservations WHERE waitlist_order IS NOT NULL",
            fetch="one",
        ).get("count", 0)

        waitlist_order = waitlist_count + 1
        waitlist_position = waitlist_order  # 초기 대기자 위치
        status = "waitlisted"

    result = execute_query(
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

    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def get_reservation_by_id(reservation_id: int) -> Optional[Dict[str, Any]]:
    """ID로 예약을 조회합니다."""
    result = execute_query(
        "SELECT * FROM reservations WHERE id = ?", (reservation_id,), fetch="one"
    )
    return dict(result) if result else None


def list_reservations(
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    is_blacklisted: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """예약 목록을 조회합니다."""
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
    return [dict(row) for row in results]


def update_reservation_status(
    reservation_id: int, status: str, approved_by: int
) -> bool:
    """예약 상태를 업데이트합니다."""
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
    """예약을 취소합니다."""
    execute_query(
        "UPDATE reservations SET status = 'cancelled' WHERE id = ?", (reservation_id,)
    )
    return True


def delete_reservation(reservation_id: int) -> bool:
    """예약을 삭제합니다."""
    execute_query("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    return True


# ==================== Blacklist Operations ====================


def add_to_blacklist(
    commander_id: str,
    nickname: Optional[str] = None,
    reason: Optional[str] = None,
    added_by: Optional[int] = None,
) -> int:
    """블랙리스트에 추가합니다."""
    result = execute_query(
        """
        INSERT INTO blacklist (commander_id, nickname, reason, added_by)
        VALUES (?, ?, ?, ?)
    """,
        (commander_id, nickname, reason, added_by),
    )

    # 기존 예약들도 블랙리스트로 표시
    execute_query(
        """
        UPDATE reservations
        SET is_blacklisted = 1, blacklist_reason = ?
        WHERE commander_id = ?
    """,
        (reason, commander_id),
    )

    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def check_blacklist(commander_id: str) -> Optional[Dict[str, Any]]:
    """블랙리스트 체크 (로컬 + Google Sheets)."""
    # 로컬 블랙리스트 체크
    result = execute_query(
        "SELECT * FROM blacklist WHERE commander_id = ? AND is_active = 1",
        (commander_id,),
        fetch="one",
    )

    if result:
        return dict(result)

    # Google Sheets 블랙리스트 체크
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

                # 사령관번호(IGG 아이디) 컬럼 찾기 (정확한 매칑)
                commander_id_str = str(commander_id)

                # ID 컬럼 우선 매칑 (정확도 높음)
                id_columns = []
                for col in df.columns:
                    col_lower = str(col).lower()
                    # 정확한 ID 컬럼만 선택
                    if (
                        col_lower == "id"
                        or col_lower == "사령관번호"
                        or (
                            col_lower.startswith("igg")
                            and not any(
                                kw in col_lower
                                for kw in ["닉네임", "이름", "연맹", "alliance", "소속"]
                            )
                        )
                    ):
                        id_columns.append(col)

                # ID 컬럼에서 정확히 매칭
                for col in id_columns:
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
                                "matched_column": col,
                            }
                    except Exception:
                        continue

                # 부분 매칭 (긴급 대안)
                for col in df.columns:
                    if any(
                        keyword in str(col).lower() for keyword in ["igg", "사령관"]
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
                                    "matched_column": col,
                                }
                        except Exception:
                            continue
    except Exception as e:
        st.warning(f"Google Sheets 블랙리스트 조회 실패: {e}")

    return None


def remove_from_blacklist(commander_id: str) -> bool:
    """블랙리스트에서 제거합니다."""
    execute_query(
        "UPDATE blacklist SET is_active = 0 WHERE commander_id = ?", (commander_id,)
    )
    return True


def list_blacklist(is_active: bool = True) -> List[Dict[str, Any]]:
    """블랙리스트 목록을 조회합니다."""
    results = execute_query(
        "SELECT * FROM blacklist WHERE is_active = ? ORDER BY added_at DESC",
        (1 if is_active else 0,),
        fetch="all",
    )
    return [dict(row) for row in results]


# ==================== Server Operations ====================


def add_server(server_name: str, server_code: Optional[str] = None) -> int:
    """서버를 추가합니다."""
    result = execute_query(
        "INSERT INTO servers (server_name, server_code) VALUES (?, ?)",
        (server_name, server_code),
    )
    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def list_servers(is_active: bool = True) -> List[Dict[str, Any]]:
    """서버 목록을 조회합니다."""
    results = execute_query(
        "SELECT * FROM servers WHERE is_active = ? ORDER BY server_name",
        (1 if is_active else 0,),
        fetch="all",
    )
    return [dict(row) for row in results]


# ==================== Alliance Operations ====================


def add_alliance(alliance_name: str, server_id: Optional[int] = None) -> int:
    """연맹을 추가합니다."""
    result = execute_query(
        "INSERT INTO alliances (alliance_name, server_id) VALUES (?, ?)",
        (alliance_name, server_id),
    )
    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def list_alliances(is_active: bool = True) -> List[Dict[str, Any]]:
    """연맹 목록을 조회합니다."""
    results = execute_query(
        "SELECT a.*, s.server_name FROM alliances a LEFT JOIN servers s ON a.server_id = s.id WHERE a.is_active = ? ORDER BY a.alliance_name",
        (1 if is_active else 0,),
        fetch="all",
    )
    return [dict(row) for row in results]


# ==================== Announcement Operations ====================


def create_announcement(
    title: str,
    content: str,
    category: str = "공지",
    is_pinned: bool = False,
    created_by: Optional[int] = None,
) -> int:
    """공지사항을 생성합니다."""
    result = execute_query(
        """
        INSERT INTO announcements (title, content, category, is_pinned, created_by)
        VALUES (?, ?, ?, ?, ?)
    """,
        (title, content, category, 1 if is_pinned else 0, created_by),
    )

    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def get_announcement_by_id(announcement_id: int) -> Optional[Dict[str, Any]]:
    """ID로 공지사항을 조회합니다."""
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
    return dict(result) if result else None


def list_announcements(
    is_active: bool = True, category: Optional[str] = None, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """공지사항 목록을 조회합니다."""
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
    return [dict(row) for row in results]


def update_announcement(
    announcement_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: Optional[str] = None,
    is_pinned: Optional[bool] = None,
    is_active: Optional[bool] = None,
) -> bool:
    """공지사항을 업데이트합니다."""
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
    """공지사항을 삭제합니다."""
    execute_query("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    return True


# ==================== Participant Operations ====================


def add_participant(data: Dict[str, Any]) -> int:
    """참여자를 추가합니다."""
    result = execute_query(
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
    return (
        result.lastrowid
        if hasattr(result, "lastrowid")
        else execute_query("SELECT last_insert_rowid()", fetch="one")[0]
    )


def list_participants(event_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """참여자 목록을 조회합니다."""
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
    return [dict(row) for row in results]


def update_participant(participant_id: int, **kwargs) -> bool:
    """참여자 정보를 업데이트합니다."""
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
    """참여자를 삭제합니다."""
    execute_query("DELETE FROM participants WHERE id = ?", (participant_id,))
    return True


# ==================== Initialization ====================


def initialize_master_account():
    """마스터 계정을 초기화합니다."""
    master_username = st.secrets.get("MASTER_USERNAME", "DaWnntt0623")
    master_password = st.secrets.get("MASTER_PASSWORD", "4425endvise9897!")

    # 마스터 계정이 없으면 생성
    existing = get_user_by_username(master_username)
    if not existing:
        create_user(
            username=master_username,
            commander_id=None,
            password=master_password,
            role="master",
            nickname="마스터 관리자",
        )
        st.success(f"마스터 계정이 생성되었습니다: {master_username}")


def init_app():
    """앱을 초기화합니다."""
    init_database()
    initialize_master_account()

    # 기본 서버 데이터 추가
    default_servers = [
        "#095 woLF",
        "#708 아시아",
    ]
    for server_name in default_servers:
        try:
            add_server(server_name, server_name.split()[0])
        except:
            pass  # 이미 존음

    # 마이그레이션: waitlist_order, waitlist_position 컬럼 추가
    # 컬럼 존재 여부 확인 후 추가
    try:
        # reservations 테이블 구조 확인
        result = execute_query("PRAGMA table_info(reservations)", fetch="all")
        existing_columns = [col["name"] for col in result]

        if "waitlist_order" not in existing_columns:
            execute_query("ALTER TABLE reservations ADD COLUMN waitlist_order INTEGER")

        if "waitlist_position" not in existing_columns:
            execute_query(
                "ALTER TABLE reservations ADD COLUMN waitlist_position INTEGER"
            )
    except Exception as e:
        st.warning(f"마이그레이션 중 오류 발생: {e}")

    # 마이그레이션: event_sessions에 예약 시간 필드 추가
    try:
        result = execute_query("PRAGMA table_info(event_sessions)", fetch="all")
        existing_columns = [col["name"] for col in result]

        if "reservation_open_time" not in existing_columns:
            execute_query(
                "ALTER TABLE event_sessions ADD COLUMN reservation_open_time DATETIME"
            )

        if "reservation_close_time" not in existing_columns:
            execute_query(
                "ALTER TABLE event_sessions ADD COLUMN reservation_close_time DATETIME"
            )
    except Exception as e:
        st.warning(f"이벤트 세션 마이그레이션 중 오류 발생: {e}")
