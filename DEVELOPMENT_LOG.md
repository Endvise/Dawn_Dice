# DaWn Dice Party - 개발 이력 및 계속 진행을 위한 기록

## 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v01 | 2026-02-03 | Sisyphus | 초기 설정 및 계획 수립 |
| v02 | 2026-02-03 | Sisyphus | 코드 리팩토링 및 신규 기능 구현 |
| v03 | 2026-02-03 | Sisyphus | 보안 강화 (.secrets/ 이동) |
| v04 | 2026-02-03 | Sisyphus | **전체 이력 작성** - oaisstart run용 |
| v05 | 2026-02-04 | Sisyphus | Supabase 스키마 확인 (users/admins/reservations/blacklist/audit_logs) |
| v06 | 2026-02-04 | Sisyphus | participants/announcements 테이블 생성 |
| v07 | 2026-02-04 | Sisyphus | **스키마 일치 작업 완료** - users/admins/reservations/blacklist/announcements 테이블에 맞게 코드 수정 |
| v06 | 2026-02-04 | Sisyphus | participants/announcements 테이블 생성 |

---

# 1. 개발 개요

## 1.1 프로젝트 목적
- **DaWn Dice Party** - 주사위 파티 이벤트 예약 시스템
- Streamlit + Python + Supabase로 전환 중
- 기존 SQLite에서 Supabase로 DB 마이그레이션

## 1.2 현재 상태
- **Phase 2, 3, 4**: ✅ 완료
- **Supabase 연동**: ✅ 완료 (스키마 확인 완료, 코드 수정 완료)
- **스키마 확인**: ✅ 완료 (2026-02-04)
- **코드 수정**: ✅ 완료 (2026-02-04)

---

# 2. Supabase 현재 상황 (가장 중요)

## 2.1 연결 상태
```
✅ service_role key: 설정됨 (.secrets/supabase_secrets.toml)
✅ 스키마: 확인 완료 (Dashboard에서 수동 확인)
⏳ 코드 수정: 대기 중
```

## 2.2 테이블 현황

| 테이블명 | 존재 | 데이터 | 코드와 일치 |
|----------|------|--------|------------|
| users | ✅ | 0개 | ✅ 일치 |
| admins | ✅ | 0개 | ✅ 일치 |
| reservations | ✅ | 0개 | ✅ 일치 (단순화) |
| blacklist | ✅ | 0개 | ✅ 일치 |
| audit_logs | ✅ | 0개 | 신규 테이블 |
| participants | ✅ | 0개 | 신규 테이블 |
| announcements | ✅ | 0개 | 신규 테이블 |

## 2.3 현재 코드에서 사용하는 스키마 (DATABASE_SCHEMA.md 기반)

### users 테이블
```python
{
    "username": "사용자ID",
    "commander_id": "사령관번호",
    "password_hash": "비밀번호해시",
    "role": "master/admin/user",
    "nickname": "닉네임",
    "server": "서버",
    "alliance": "연맹",
    "is_active": True/False,
    "created_at": "생성일시",
    "last_login": "마지막로그인",
    "failed_attempts": 0,
}
```

### reservations 테이블
```python
{
    "user_id": 1,
    "nickname": "닉네임",
    "commander_id": "사령관번호",
    "server": "서버",
    "alliance": "연맹",
    "status": "pending/approved/rejected/cancelled/waitlisted",
    "is_blacklisted": False,
    "blacklist_reason": None,
    "created_at": "생성일시",
    "approved_at": None,
    "approved_by": None,
    "notes": None,
    "waitlist_order": None,
    "waitlist_position": None,
}
```

## 2.4 실제 Supabase 테이블 컬럼명 (2026-02-04 확인)

### users 테이블
| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | uuid | PK |
| commander_number | character varying | ID로 사용 |
| password_hash | text | |
| nickname | text | |
| server | text | |
| alliance | text | |
| is_active | boolean | |
| created_at | timestamp with time zone | |
| updated_at | timestamp with time zone | |

**코드 차이점:**
- ❌ `username` 없음 → `commander_number`가 ID
- ❌ `role` 없음 (별도 admins 테이블로 분리)
- ❌ `last_login`, `failed_attempts` 없음

---

### admins 테이블 (신규)
| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | uuid | PK |
| username | text | |
| password_hash | text | |
| full_name | text | |
| role | text | master/admin |
| created_at | timestamp with time zone | |
| last_login_at | timestamp with time zone | |

**참고:** 관리자 계정이 별도 테이블로 분리됨

---

### reservations 테이블
| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | uuid | PK |
| user_id | uuid | users.id 연결 |
| commander_number | character varying | |
| nickname | text | |
| server | text | |
| notes | text | |
| reserved_by | uuid | admins.id 연결 |
| created_at | timestamp with time zone | |
| reserved_at | timestamp with time zone | |

**코드 차이점:**
- ❌ `status` 없음 (단순 예약만)
- ❌ `alliance` 없음
- ❌ `is_blacklisted`, `blacklist_reason` 없음
- ❌ `approved_at`, `approved_by` 없음
- ❌ `waitlist_order`, `waitlist_position` 없음

---

### blacklist 테이블
| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | uuid | PK |
| user_id | uuid | users.id 연결 |
| commander_number | character varying | |
| nickname | text | |
| server | text | |
| reason | text | |
| blacklisted_by | uuid | admins.id 연결 |
| created_at | timestamp with time zone | |
| expires_at | timestamp with time zone | 만료일 |

**코드 차이점:**
- `created_by` → `blacklisted_by`
- `expires_at` 추가 (만료 기능)

---

### audit_logs 테이블 (신규)
| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | uuid | PK |
| actor_role | text | |
| actor_id | uuid | |
| action | text | |
| target_table | text | |
| target_id | uuid | |
| details | jsonb | |
| created_at | timestamp with time zone | |

---

### 존재하지 않는 테이블
| 테이블 | 상태 |
|--------|------|
| (없음) | 모든 테이블 존재 |

---

# 3. 완료된 작업 상세

## 3.1 Phase 2: 코드 리팩토링 ✅

### config.py (신규 생성)
```python
# 위치: dice_app/config.py
# 용도: Supabase/설정 중앙化管理

SECRETS_PATHS = [
    Path(".secrets/supabase_secrets.toml"),  # 최우선 (gitignored)
    Path(".streamlit/secrets.toml"),  # Streamlit 기본
]

def get_config():
    return {
        "db_type": "supabase",
        "supabase": {...},
        "auth": {...},
        "security": {...},
        "session": {...},
    }
```

### database.py (리팩토링)
```python
# 변경 전
from supabase import create_client
_SUPABASE_URL = "..."
_SUPABASE_KEY = "..."

# 변경 후
import config
from config import get_config, get_headers, get_supabase_url
```

### auth.py (간소화)
```python
# 변경 전
use_supabase_auth = st.secrets.get("USE_SUPABASE_AUTH", False)
max_attempts = st.secrets.get("MAX_LOGIN_ATTEMPTS", 5)

# 변경 후
auth_config = config.get_config()['auth']
max_attempts = auth_config['max_login_attempts']
```

## 3.2 Phase 3: 신규 기능 구현 ✅

### public_status.py (신규)
```python
# 위치: dice_app/views/public_status.py
# 용도: 외부인에게 예약 현황 공개
# 기능:
# - 현재 예약 세션 표시
# - 예약 가능/마감 상태
# - 정원 현황 (N/M)
# - 대기자 수
```

### excel_uploader.py (신규)
```python
# 위치: dice_app/utils/excel_uploader.py
# 기능 1: Excel → Supabase 업로드
TABLE_MAPPINGS = {
    "users": {"사령관번호": "commander_id", ...},
    "participants": {...},
    "blacklist": {"사령관번호": "commander_id", ...},
    "reservations": {...},
}

# 기능 2: Google Sheets 블랙리스트 동기화
def sync_blacklist_from_google_sheets():
    # Google Sheets에서 블랙리스트 가져와 Supabase에 저장
```

### admin_reservation_settings.py (신규)
```python
# 위치: dice_app/views/admin_reservation_settings.py
# 기능:
# - 예약 상태 제어 (오픈/마감)
# - 예약 시간 설정
# - 예약 현황 통계
# - 예약자 명단 관리
```

## 3.3 Phase 4: 스키마 수정 ✅

### commander_number → commander_id 변경
```bash
# 변경된 파일:
dice_app/database.py       ✅
dice_app/auth.py           ✅
dice_app/utils/excel_uploader.py  ✅
dice_app/views/admin_reservation_settings.py  ✅
```

---

# 4. 보안 강화 (.secrets/ 이동)

## 4.1 이전 구조 (위험)
```
.streamlit/secrets.toml  ← Git에 포함될 위험
```
실제 API 키가 Git 추적 대상에 있음

## 4.2 현재 구조 (안전)
```
.secrets/
└── supabase_secrets.toml  ← Git 추적 안됨 (.gitignore)
.streamlit/secrets.toml    ← 템플릿만 존재 (실제 키 없음)
```

## 4.3 .gitignore 추가 내용
```gitignore
# Supabase keys - NEVER commit!
.secrets/
*secrets*
*service_role*
sb_*
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9*
```

## 4.4 config.py 우선순위
```python
SECRETS_PATHS = [
    Path(".secrets/supabase_secrets.toml"),  # 1순위 (로컬 개발용)
    Path(".streamlit/secrets.toml"),  # 2순위 (Streamlit Cloud용)
]
```

---

# 5. 생성된 파일 목록

## 5.1 코드 파일 (Git 추적 ✅)

| 파일 경로 | 용도 | 상태 |
|----------|------|------|
| `dice_app/config.py` | 설정 중앙화 | ✅ 완료 |
| `dice_app/views/public_status.py` | 예약 현황 공개 UI | ✅ 완료 |
| `dice_app/utils/excel_uploader.py` | Excel 업로드 + 동기화 | ✅ 완료 |
| `dice_app/views/admin_reservation_settings.py` | 관리자 예약 설정 | ✅ 완료 |
| `dice_app/database.py` | DB 연산 (리팩토링) | ✅ 완료 |
| `dice_app/auth.py` | 인증 (리팩토링) | ✅ 완료 |

## 5.2 문서 파일 (Git 추적 ✅)

| 파일 경로 | 용도 |
|----------|------|
| `oaisplan.md` | 전체 개발 계획서 |
| `PROGRESS_REPORT.md` | 진행 상황 보고서 |
| `DEVELOPMENT_LOG.md` | **본 파일** - 전체 이력 |

## 5.3 보안 파일 (Git 추적 ❌)

| 파일 경로 | 용도 | 주의사항 |
|----------|------|----------|
| `.secrets/supabase_secrets.toml` | 실제 API 키 | Git 추적 안됨 |

## 5.4 템플릿 파일 (Git 추적 ✅)

| 파일 경로 | 용도 |
|----------|------|
| `.streamlit/secrets.toml` | secrets 템플릿 |

## 5.5 테스트 파일 (Git 추적 ✅)

| 파일 경로 | 용도 |
|----------|------|
| `test_supabase_connection.py` | Supabase 연결 테스트 |

---

# 6. oaisstart run으로 다시 시작할 때

## 6.1 첫 번째로 확인할 것

```bash
# 1. secrets 파일 존재 확인
cat .secrets/supabase_secrets.toml

# 2. Supabase 연결 테스트
python test_supabase_connection.py

# 3. 현재 상태 확인
python -c "
import requests
with open('.secrets/supabase_secrets.toml') as f:
    content = f.read()
# service_role key가 설정되어 있는지 확인
"
```

## 6.2 현재 진행해야 할 작업

### 작업 1: Supabase Dashboard에서 스키마 확인 ✅ 완료
```
URL: https://supabase.com/dashboard/project/gticuuzplbemivfturuz

확인된 테이블: users, admins, reservations, blacklist, audit_logs
```

### 작업 2: 코드 수정 (스키마 일치시키기) ⏳ 진행 중
```python
# users 테이블 컬럼명이 'username'이 아니라 'email'이라면
# dice_app/database.py의 create_user() 함수에서:

# 변경 전
data = {
    "username": username,
    "commander_id": commander_id,
    ...
}

# 변경 후
data = {
    "email": username,  # 또는 실제 컬럼명
    "commander_id": commander_id,
    ...
}
```

### 작업 3: INSERT 테스트
```python
# Supabase에서 직접 테스트
# Table Editor에서 수동으로 데이터 추가해보기
```

### 작업 4: 전체 테스트
```bash
# Streamlit 앱 실행
streamlit run dice_app/app.py

# 테스트 내용:
# 1. 마스터 계정으로 로그인
# 2. 사용자 회원가입
# 3. 예약 신청
```

---

# 7. 자주 발생하는 오류 및 해결법

## 7.1 INSERT 실패 (PGRST204)
```
{"code":"PGRST204","message":"Could not find the 'xxx' column"}
```
**해결:** 컬럼명이 코드와 다름. Dashboard에서 실제 컬럼명 확인 후 코드 수정

## 7.2 401 Unauthorized
```
{"code":"401","message":"Invalid API key"}
```
**해결:** service_role key가 없거나 만료됨. Dashboard에서 새로운 key 발급

## 7.3 테이블 없음 (PGRST205)
```
{"code":"PGRST205","message":"Could not find the table"}
```
**해결:** Table Editor에서 테이블 생성 필요

---

# 8. 참고 URL

| 항목 | URL |
|------|-----|
| Supabase Dashboard | https://supabase.com/dashboard/project/gticuuzplbemivfturuz |
| 프로젝트 GitHub | https://github.com/Endvise/Dawn_Dice |
| 로컬 개발 문서 | `oaisplan.md`, `PROGRESS_REPORT.md`, `DEVELOPMENT_LOG.md` (본 파일) |

---

# 9. 체크리스트 (oaisstart run 후 확인용)

## 9.1 환경 설정
- [ ] `.secrets/supabase_secrets.toml` 존재 확인
- [ ] `SERVICE_ROLE_KEY` 설정 확인
- [ ] `python test_supabase_connection.py` 통과 확인

## 9.2 Supabase 연동
- [x] Dashboard에서 실제 스키마 확인 (2026-02-04)
- [x] 코드와 스키마 일치시키기 (2026-02-04)
- [ ] INSERT 테스트 통과 확인
- [ ] 마스터 계정 로그인 테스트

## 9.3 전체 기능 테스트
- [ ] 예약 현황 페이지 확인
- [ ] Excel 업로드 기능 테스트
- [ ] 블랙리스트 동기화 테스트
- [ ] 관리자 페이지 동작 확인

---

# 10. 연락처 및 참고

- **프로젝트 관리자**: 엔티티
- **기술 스택**: Streamlit, Python, Supabase, bcrypt

---

*본 문서는 2026-02-03에 작성됨*
*2026-02-04: 스키마 정보 업데이트*
*2026-02-04: 코드 수정 완료 (스키마 일치)*
*oaisstart run 시 반드시 참고할 것*

---

# 11. 코드 수정 요약 (2026-02-04)

## 11.1 database.py 수정

### users 테이블
- `username` → `commander_number`로 변경
- `role` 컬럼 제거 (admins 테이블로 이동)
- `last_login`, `failed_attempts` 컬럼 제거
- `commander_id` → `commander_number` 컬럼명 변경

### admins 테이블 (신규)
- 관리자 계정 관련 함수 추가:
  - `create_admin`
  - `get_admin_by_username`
  - `get_admin_by_id`
  - `list_admins`
  - `update_admin_last_login`
  - `delete_admin`
- `_init_master_account`에서 users → admins 테이블 사용

### reservations 테이블
- `status`, `alliance`, `is_blacklisted`, `blacklist_reason`, `approved_at`, `approved_by` 컬럼 제거
- `waitlist_order`, `waitlist_position` 제거 (대기자 시스템 단순화)
- `reserved_at` 컬럼 추가
- `create_reservation` 함수 단순화

### blacklist 테이블
- `added_by` → `blacklisted_by` 컬럼명 변경
- `is_active` 컬럼 제거
- `expires_at` 컬럼 추가
- `check_blacklist`에서 만료일 체크 추가

---

## 11.2 auth.py 수정

### login 함수
- 먼저 `admins` 테이블 확인 (master/admin)
- 그 다음 `users` 테이블 확인 (일반 사용자)
- `failed_attempts`, `last_login` 로직 제거
- `role`은 session에서만 관리 (users 테이블에는 없음)

### 기타 함수
- `show_user_info`: role 필드 직접 참조 대신 session에서 가져옴
- `get_user_statistics`: status 필드 관련 로직 제거

---

## 11.3 views/admin_dashboard.py 수정

### get_dashboard_stats 함수
- `admin_users` → `list_admins(role="admin")`로 변경
- reservations의 status 필터링 제거 (단순화된 스키마)
- blacklist의 `is_active` 파라미터 제거

### User List 탭
- `role` 필드 참조 제거 (users는 모두 "user")
- `last_login`, `failed_attempts` 필드 제거
- `commander_id` → `commander_number`로 변경

### Blacklist List 탭
- `is_active=True` 파라미터 제거
- `commander_id` → `commander_number`로 변경
- `added_at` → `created_at`로 변경
- `expires_at` 추가

---

## 11.4 views/public_status.py 수정

- `waitlist_count = 0`으로 고정 (대기자 시스템 없음)

---

## 11.5 views/admin_reservation_settings.py 수정

### show_reservation_settings 함수
- `pending_count`, `waitlisted_count`, `rejected_count`를 0으로 고정

### show_reservation_list 함수
- status 필터 UI 제거
- blacklist 필터 UI 제거
- `commander_id` → `commander_number`로 변경
- `status`, `is_blacklisted` 컬럼 제거
- 승인/거절 버튼 제거 (status가 없으므로)
- 삭제 버튼으로 대체
