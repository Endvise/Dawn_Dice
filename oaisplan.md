# DaWn Dice Party - 통합 개발 계획서

## 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v01 | 2026-02-03 | Sisyphus | 초기 작성 - 문제 분석 및 계획 수립 |

---

## 1. 현재 문제점 분석

### 1.1 Supabase 연동 실패 원인

현재 Streamlit 앱에서 Supabase로의 데이터 전송이 실패하는 주요 원인은 다음과 같이 분석되었다. 첫째, secrets.toml에 설정된 `SUPABASE_KEY`가 **publishable key (anon key)**이다. 이 키는 읽기 전용 권한만 가지고 있어 INSERT, UPDATE, DELETE 같은 쓰기 작업이 모두 실패한다. 둘째, 코드에서는 `database.py`의 `insert()`, `update()`, `delete()` 함수들이 정상적으로 구현되어 있으나, 키 권한 부족으로 인해 작동하지 않는 상황이다.

현재 secrets.toml에 설정된 값들을 확인하면 `SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"`와 `SUPABASE_KEY = "sb_publishable_Z53hNS_FW1c4Bi5BVwDxfQ_mMH1wP0-"`로 되어 있다. 이 publishable key로는 SELECT 쿼리만 가능하며, 쓰기 작업 시 401 Unauthorized 에러가 발생한다.

사용자가 제공한 MCP URL `https://mcp.supabase.com/mcp?project_ref=gticuuzplbemivfturuz...`은 Supabase MCP (Model Context Protocol) 서버용 URL이다. 이는 AI 에이전트가 Supabase와 통신하기 위한 별도 경로이며, Streamlit 앱에서 직접 Supabase SDK로 연결할 때는 사용하지 않는다. Streamlit 앱은 직접 Supabase REST API 또는 SDK를 통해 통신해야 한다.

### 1.2 인증 및 회원가입 실패 증상

마스터 계정 및 사용자 가입 테스트가 실패하는 현상은 다음과 같은 복합적 원인으로 분석된다. 첫째, 쓰기 권한이 없으므로 회원가입 시 `insert("users", data)` 호출이 실패한다. 둘째, 마스터 계정 초기화 함수 `_init_master_account()`도 동일한 문제를 겪는다. 셋째, 기존에 SQLite로 구현되었던 코드에서 Supabase로 전환하면서 키 설정만 변경하고 실제 권한 문제를 해결하지 않았다.

### 1.3 코드 중복 및 개선 필요 영역

현재 코드베이스를 검토한 결과 몇 가지 개선이 필요한 영역이 확인되었다. `database.py` 파일이 802줄로 상당히 비대하며, SQLite와 Supabase를 동시에 지원하려다 복잡성이 증가했다. `auth.py` 파일은 270줄로 적절한 크기이나, Supabase Auth와 자체 인증을 병행하려다 로직이 복잡해졌다.

주요 중복 및 개선 필요 사항으로는 먼저 REST API 호출 함수인 `supabase_request()`가 중복해서 정의되어 있다. 그리고 API 키 관리가 `_get_config()` 함수에 집중되어 있으나 하드코딩된 기본값이 섞여 있다. 또한 주석과 실제 코드가 일치하지 않는 부분이 있으며, 주석에는 Supabase Auth 모듈 지원이 언급되어 있으나 실제 구현은 불완전하다.

---

## 2. Supabase 연동 문제 해결 계획

### 2.1 service_role key获取 및 설정

Supabase Dashboard에서 service_role key를 발급받아 secrets.toml에 설정해야 한다. Supabase Dashboard (https://supabase.com/dashboard)에 접속하여 프로젝트 `gticuuzplbemivfturuz`를 선택한다.左侧菜单에서 **Settings** → **API**를 선택한다. **API Settings** 페이지에서 **service_role** 섹션을 찾고 **Copy** 버튼을 클릭하여 키를 복사한다. 이 키는 절대 공개되어서는 안 되며, 클라이언트 측에서 사용하면 안 된다.

secrets.toml 파일을 다음과 같이 수정한다.

```toml
# ============================================
# Supabase 설정 (수정됨)
# ============================================
SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0aWN1dXpsbGVtLXZmdHVydXoiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTczMDAwMDAwMCwiZXhwIjoyMDQ1NTc2MDAwfQ.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # 실제 service_role key로 교체
SERVICE_ROLE_KEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # service_role key 별도 저장
USE_SUPABASE_AUTH = false
```

### 2.2 RLS (Row Level Security) 정책 확인

Supabase Dashboard의 **Authentication** → **Policies**에서 각 테이블의 RLS 정책을 확인해야 한다. users, reservations, blacklist, participants 테이블에 대해 적절한 RLS 정책이 설정되어 있는지 점검한다. service_role key 사용 시에는 RLS가 우회되므로 개발 환경에서는 이方式来 테스트하고, 프로덕션에서는 RLS 정책을 정확히 설정하는 것을 권장한다.

### 2.3 연결 테스트 스크립트 작성

Supabase 연결을 검증하기 위한 테스트 스크립트를 작성한다.

```python
#!/usr/bin/env python3
"""
Supabase 연결 테스트 스크립트
"""
import requests

SUPABASE_URL = "https://gticuuzplbemivfturuz.supabase.co"
SUPABASE_KEY = "your_service_role_key"  # service_role key

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# 1. 연결 테스트
print("1. 연결 테스트...")
response = requests.get(f"{SUPABASE_URL}/rest/v1/users?select=id&limit=1", headers=headers)
print(f"   상태 코드: {response.status_code}")
print(f"   응답: {response.text[:200]}")

# 2. INSERT 테스트
print("\n2. INSERT 테스트...")
test_data = {
    "username": "test_user",
    "commander_number": "TEST1234567",
    "password_hash": "test_hash",
    "role": "user",
    "nickname": "Test",
}
response = requests.post(f"{SUPABASE_URL}/rest/v1/users", headers=headers, json=test_data)
print(f"   상태 코드: {response.status_code}")
print(f"   응답: {response.text[:200]}")
```

---

## 3. 코드 개선 계획

### 3.1 database.py 리팩토링

`database.py` 파일을 다음과 같이 구조화하여 개선한다. 먼저 설정 관리를 별도 모듈로 분리하여 `config.py` 파일을 생성하고 Supabase URL, API 키, 환경별 설정을 관리한다. 다음으로 데이터베이스 연산을 `operations/` 디렉토리에 분리하여 user_operations.py, reservation_operations.py, blacklist_operations.py, participant_operations.py로 나눈다. 마지막으로 공통 유틸리티를 `utils/` 디렉토리에 배치하여 supabase_client.py, excel_utils.py, validators.py로 분리한다.

```python
# dice_app/config.py
"""
Configuration Management Module
"""
import streamlit as st

def get_supabase_config():
    """Get Supabase configuration from secrets."""
    return {
        "url": st.secrets.get("SUPABASE_URL"),
        "anon_key": st.secrets.get("SUPABASE_KEY"),
        "service_role_key": st.secrets.get("SERVICE_ROLE_KEY"),
        "use_auth": st.secrets.get("USE_SUPABASE_AUTH", False),
    }

def get_database_config():
    """Get database configuration."""
    return {
        "db_type": st.secrets.get("DB_TYPE", "supabase"),
        "db_path": st.secrets.get("DB_PATH", "data/dice_app.db"),
    }
```

### 3.2 auth.py 간소화

현재 auth.py는 Supabase Auth와 자체 인증을 동시에 지원하려다 복잡해졌다. 단일 인증 방식으로 통일하여 간소화한다.

| 설정값 | 현재 동작 | 제안 변경 |
|--------|---------|----------|
| USE_SUPABASE_AUTH = false | users 테이블 기반 자체 인증 | 유지 |
| USE_SUPABASE_AUTH = true | Supabase Auth 사용 | 제거 (복잡성 증가) |

### 3.3 중복 코드 제거 및 통합

현재 코드베이스에서 발견된 중복 사항을 제거한다. 먼저 JSON 임포트 임포트 관련하여 `database.py`의 `import json`은 사용되지 않아 제거한다. requests 모듈 관련하여 `check_blacklist()` 함수 내에서 `import requests as req`가 중복되어 함수 상단으로 이동한다. 주석 관련하여 `database.py`의 주석에는 Supabase Auth 모듈 지원이 언급되어 있으나 실제 구현은 불완전하므로 주석을 정확하게 수정한다.

---

## 4. 신규 기능 구현 계획

### 4.1 외부인 예약 가능 여부 UI

외부인이 현재 예약 가능 상태인지 확인 할 수 있는 UI를 구현한다. 이 기능은 비로그인 사용자도 접근할 수 있어야 하며, 현재 예약 상태(마감, 대기 가능, 오픈 예정)를 표시한다.

```python
# dice_app/views/public_status.py
"""
Public Reservation Status Page
비로그인 사용자도 확인할 수 있는 예약 상태 페이지
"""
import streamlit as st
import database as db

def show_public_status():
    """Display public reservation status."""
    st.title("🎲 DaWn Dice Party - 예약 현황")

    # 현재 세션 정보
    active_session = db.get_active_session()
    if not active_session:
        st.info("현재 진행 중인 예약 세션이 없습니다.")
        return

    # 예약 가능 여부
    is_open = active_session.get("is_reservation_open", False)
    if not is_open:
        st.warning("현재 예약이 마감되었습니다.")
        # 예약 오픈 시간 안내
        open_time = active_session.get("reservation_open_time")
        close_time = active_session.get("reservation_close_time")
        if open_time:
            st.info(f"예약 오픈 시간: {open_time}")
        return

    # 통계 정보
    approved_count = db.get_approved_reservation_count(active_session["id"])
    max_participants = active_session.get("max_participants", 180)
    remaining = max_participants - approved_count

    # 상태 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("예약 현황", f"{approved_count} / {max_participants}")
    with col2:
        if remaining > 0:
            st.success(f"예약 가능! ({remaining}명 남음)")
        else:
            st.error("정원 초과 - 대기 등록만 가능")
    with col3:
        waitlist_count = db.get_waitlist_count()
        st.info(f"대기자: {waitlist_count}명")

    # 대기 등록 안내
    if remaining <= 0:
        st.info("정원이 초과되었습니다. 대기 등록을 이용해주세요.")
```

### 4.2 Excel → CSV → Supabase 자동 업로드 기능

엑셀 파일을 업로드하면 Supabase 테이블 형식에 맞춰 데이터를 변환하여 자동 업로드하는 기능을 구현한다.

```python
# dice_app/utils/excel_uploader.py
"""
Excel to Supabase Uploader
엑셀 파일을 읽어서 Supabase에 자동 업로드
"""
import streamlit as st
import pandas as pd
import database as db
from typing import Dict, List, Optional

# 테이블별 컬럼 매핑
TABLE_MAPPINGS = {
    "users": {
        "사령관번호": "commander_number",
        "닉네임": "nickname",
        "서버": "server",
        "연맹": "alliance",
        "비밀번호": "password_hash",
    },
    "participants": {
        "번호": "number",
        "닉네임": "nickname",
        "소속": "affiliation",
        "IGG ID": "igg_id",
        "연맹": "alliance",
        "이벤트명": "event_name",
        "참여완료": "completed",
    },
    "blacklist": {
        "사령관번호": "commander_number",
        "닉네임": "nickname",
        "사유": "reason",
    },
    "reservations": {
        "닉네임": "nickname",
        "사령관번호": "commander_number",
        "서버": "server",
        "연맹": "alliance",
        "상태": "status",
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
        "users": ["commander_number", "password_hash"],
        "participants": ["nickname"],
        "blacklist": ["commander_number"],
        "reservations": ["commander_number", "nickname"],
    }
    required = required_fields.get(table_name, [])
    for field in required:
        if field not in df.columns:
            errors.append(f"필수 컬럼 '{field}'이(가) 없습니다.")
    return len(errors) == 0, errors

def upload_excel_to_supabase(
    uploaded_file,
    table_name: str,
    skip_rows: int = 0,
) -> Dict:
    """Upload Excel file to Supabase."""
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(uploaded_file, skiprows=skip_rows)
        st.write(f"### 읽은 데이터 ({len(df)}행)")
        st.dataframe(df.head())

        # 컬럼명 정규화
        df = normalize_column_names(df, table_name)
        st.write(f"### 정규화된 컬럼")
        st.write(list(df.columns))

        # 데이터 검증
        is_valid, errors = validate_data(df, table_name)
        if not is_valid:
            return {"success": False, "errors": errors}

        # Supabase에 업로드
        records = df.to_dict("records")
        uploaded_count = 0
        for record in records:
            result = db.insert(table_name, record)
            if result:
                uploaded_count += 1

        return {
            "success": True,
            "uploaded": uploaded_count,
            "total": len(records),
        }

    except Exception as e:
        return {"success": False, "errors": [str(e)]}

# 관리자 페이지에 추가할 UI 코드
def show_excel_upload_page():
    """Excel Upload Admin Page."""
    st.title("📤 Excel → Supabase 업로드")

    # 테이블 선택
    table = st.selectbox(
        "업로드할 테이블 선택",
        ["users", "participants", "blacklist", "reservations"]
    )

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "엑셀 파일 선택 (.xlsx, .csv)",
        type=["xlsx", "csv"]
    )

    if uploaded_file:
        # 미리보기
        if st.checkbox("데이터 미리보기"):
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.dataframe(df.head(10))

        # 업로드 옵션
        skip_rows = st.number_input("건너뛸 행 수", min_value=0, value=0)

        # 업로드 버튼
        if st.button("🚀 Supabase에 업로드", type="primary"):
            with st.spinner("업로드 중..."):
                result = upload_excel_to_supabase(
                    uploaded_file,
                    table,
                    skip_rows=skip_rows,
                )

            if result["success"]:
                st.success(
                    f"업로드 완료! {result['uploaded']}/{result['total']}행"
                )
            else:
                st.error("업로드 실패:")
                for error in result.get("errors", []):
                    st.write(f"- {error}")
```

### 4.3 Google Sheets 블랙리스트 자동 동기화

외국인이 관리하는 Google Sheets 블랙리스트를 정기적으로 동기화하는 기능을 구현한다.

```python
# dice_app/utils/blacklist_sync.py
"""
Blacklist Synchronization
Google Sheets → Supabase 블랙리스트 동기화
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import StringIO
import database as db

def sync_blacklist_from_google_sheets():
    """Sync blacklist from Google Sheets to Supabase."""
    sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
    if not sheet_url:
        return {"success": False, "error": "Google Sheets URL이 설정되지 않음"}

    try:
        # Google Sheets에서 데이터 가져오기
        response = requests.get(sheet_url)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}

        # CSV로 읽기
        try:
            df = pd.read_csv(StringIO(response.text), on_bad_lines="skip")
        except Exception:
            df = pd.read_csv(
                StringIO(response.text),
                on_bad_lines="skip",
                encoding="utf-8-sig",
            )

        # 사령관번호 컬럼 찾기
        commander_col = None
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ["commander_number", "commander_id", "사령관번호", "igg_id"]:
                commander_col = col
                break

        if not commander_col:
            return {"success": False, "error": "사령관번호 컬럼을 찾을 수 없음"}

        # 기존 블랙리스트와 비교
        existing = db.list_blacklist(is_active=True)
        existing_ids = {item["commander_number"] for item in existing}

        # 새 항목 업로드
        new_count = 0
        for _, row in df.iterrows():
            commander_id = str(row[commander_col]).strip()
            if commander_id and commander_id not in existing_ids:
                db.add_to_blacklist(
                    commander_number=commander_id,
                    nickname=str(row.get("nickname", "")).strip() or None,
                    reason=f"Google Sheets 동기화 - {datetime.now().strftime('%Y-%m-%d')}",
                )
                new_count += 1

        return {
            "success": True,
            "new_entries": new_count,
            "total_in_sheet": len(df),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 4.4 관리자 페이지 기능 확장

관리자 페이지에 다음 기능을 추가한다.

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 예약 가능 UI 제어 | 예약 오픈/마감 토글 버튼 | ⭐⭐⭐ |
| 예약 오픈 시간 설정 | datetime picker로 시간 설정 | ⭐⭐⭐ |
| 회원 관리 | 사용자 목록, 활성화/비활성화 | ⭐⭐ |
| 예약자 명단 관리 | 승인/거절/대기 관리 | ⭐⭐⭐ |
| 블랙리스트 관리 | 추가/삭제/동기화 | ⭐⭐⭐ |
| Excel 업로드 | 엑셀 → Supabase 일괄 업로드 | ⭐⭐ |

```python
# dice_app/views/admin_reservation_settings.py
"""
Admin Reservation Settings Page
"""
import streamlit as st
import database as db
from datetime import datetime

def show_reservation_settings():
    """Reservation Settings Admin Page."""
    st.title("⚙️ 예약 설정 관리")

    # 현재 활성화된 세션
    session = db.get_active_session()
    if not session:
        st.warning("활성화된 세션이 없습니다.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("예약 상태")
        is_open = session.get("is_reservation_open", False)

        if is_open:
            st.success("예약 오픈됨")
            if st.button("🔒 예약 마감", type="primary"):
                db.update_session_active(session["id"], False)
                st.rerun()
        else:
            st.error("예약 마감됨")
            if st.button("🔓 예약 오픈", type="primary"):
                db.update_session_active(session["id"], True)
                st.rerun()

    with col2:
        st.subheader("예약 시간 설정")
        open_time = st.text_input(
            "예약 오픈 시간",
            value=session.get("reservation_open_time", ""),
            placeholder="YYYY-MM-DD HH:MM"
        )
        close_time = st.text_input(
            "예약 마감 시간",
            value=session.get("reservation_close_time", ""),
            placeholder="YYYY-MM-DD HH:MM"
        )

        if st.button("💾 시간 저장"):
            db.update_session_times(session["id"], open_time, close_time)
            st.success("저장됨")

    st.markdown("---")
    st.subheader("📊 현재 예약 현황")

    # 통계
    approved = db.get_approved_reservation_count(session["id"])
    pending = len(db.list_reservations(status="pending"))
    waitlisted = len(db.list_reservations(status="waitlisted"))
    max_part = session.get("max_participants", 180)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("승인됨", approved, f"{max_part - approved}남음")
    col2.metric("대기 중", pending)
    col3.metric("대기자", waitlisted)
    col4.metric("정원", f"{approved}/{max_part}")

    # 진행률 바
    progress = min(approved / max_part, 1.0)
    st.progress(progress)
```

---

## 5. 구현 일정 및 우선순위

### 5.1 Phase 1: 긴급 수정 (1-2일)

| 작업 | 내용 | 예상 시간 |
|------|------|----------|
| service_role key 설정 | secrets.toml에 키 추가 | 30분 |
| 연결 테스트 | Supabase 연결 확인 | 1시간 |
| 마스터 계정 초기화 테스트 | 마스터 로그인 확인 | 1시간 |

### 5.2 Phase 2: 코드 정리 (2-3일)

| 작업 | 내용 | 예상 시간 |
|------|------|----------|
| database.py 리팩토링 | 설정/연산 분리 | 4시간 |
| auth.py 간소화 | 인증 로직 정리 | 2시간 |
| 중복 코드 제거 | 불필요한 임포트/함수 정리 | 1시간 |
| 주석 정확화 | 코드와 주석 일치시킴 | 1시간 |

### 5.3 Phase 3: 신규 기능 (3-4일)

| 작업 | 내용 | 예상 시간 |
|------|------|----------|
| 예약 현황 공개 UI | 비로그인 예약 상태 페이지 | 3시간 |
| Excel 업로드 기능 | 엑셀 → Supabase 변환/업로드 | 6시간 |
| 블랙리스트 동기화 | Google Sheets → Supabase | 4시간 |
| 관리자 설정 확장 | 예약 시간/상태 제어 | 4시간 |

### 5.4 총 일정

| Phase | 작업 | 예상 기간 |
|-------|------|----------|
| Phase 1 | 긴급 수정 | 1-2일 |
| Phase 2 | 코드 정리 | 2-3일 |
| Phase 3 | 신규 기능 | 3-4일 |
| **총계** | | **6-9일** |

---

## 6. 검증 체크리스트

### 6.1 Supabase 연동 검증

- [ ] service_role key가 secrets.toml에 설정됨
- [ ] 연결 테스트 스크립트가 200 OK를 반환함
- [ ] INSERT/UPDATE/DELETE 작업이 정상 작동함
- [ ] 마스터 계정으로 로그인 가능함
- [ ] 사용자 회원가입이 가능함

### 6.2 기능 검증

- [ ] 예약 현황 페이지가 비로그인 상태에서 표시됨
- [ ] Excel 파일 업로드가 정상 작동함
- [ ] 컬럼명이 올바르게 정규화됨
- [ ] Google Sheets 블랙리스트 동기화가 작동함
- [ ] 관리자 페이지에서 예약 상태를 토글할 수 있음
- [ ] 예약 오픈/마감 시간이 올바르게 저장됨

### 6.3 보안 검증

- [ ] service_role key가 클라이언트에 노출되지 않음
- [ ] RLS 정책이 적절히 설정됨
- [ ] 블랙리스트 검증이 회원가입 시 작동함
- [ ] 로그인 실패 제한이 작동함

---

## 7. 리스크 및 대응 방안

### 7.1 기술적 리스크

| 리스크 | 발생 가능성 | 영향 | 대응 방안 |
|--------|-------------|------|----------|
| service_role key 유출 | 낮음 | 매우 높음 | secrets.toml을 .gitignore에 추가, Rotate 정기적 수행 |
| RLS 정책 오류 | 중간 | 높음 | 개발 환경에서 충분히 테스트 |
| 엑셀 형식 불일치 | 중간 | 중간 | 유연한 컬럼명 매핑, 오류 메시지 명확히 |
| Google Sheets 접근 실패 | 중간 | 낮음 | 로컬 블랙리스트로 폴백 |

### 7.2 운영 리스크

| 리스크 | 발생 가능성 | 영향 | 대응 방안 |
|--------|-------------|------|----------|
| Supabase 무료 할당량 초과 | 낮음 | 중간 | 사용량 모니터링, 알림 설정 |
| 동시 접속 제한 | 낮음 | 중간 | 연결 풀링 최적화 |

---

## 8. 참조 자료

### 8.1 Supabase 문서

- Supabase REST API: https://supabase.com/docs/guides/api
- Row Level Security: https://supabase.com/docs/guides/auth/row-level-security
- Service Role Keys: https://supabase.com/docs/guides/api/api-keys

### 8.2 기존 문서

- 구현 계획: `dice_app/IMPLEMENTATION_PLAN.md`
- 데이터베이스 스키마: `dice_app/DATABASE_SCHEMA.md`
- 보안 가이드: `dice_app/SECURITY_GUIDE.md`

---

## 9. 다음 단계

1. **즉시 실행**: Supabase Dashboard에서 service_role key 발급 및 secrets.toml 업데이트
2. **연결 테스트**: 테스트 스크립트로 Supabase 연결 확인
3. **마스터 계정 테스트**: 마스터 로그인 및 회원가입 테스트
4. **코드 리팩토링**: database.py, auth.py 정리
5. **신규 기능 구현**: 예약 현황 페이지, Excel 업로드 등

---

*본 문서는 oaisplan에 의해 자동 생성되었습니다.*
*생성일: 2026-02-03*
