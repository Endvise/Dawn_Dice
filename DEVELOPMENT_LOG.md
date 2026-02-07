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
| v08 | 2026-02-04 | Sisyphus | 영어 UI 적용 (home.py), None 처리 추가 |
| v09 | 2026-02-05 | Sisyphus | **비밀번호 변경 기능 추가** - 사용자/관리자 기존 비밀번호 인증 후 새 비밀번호로 변경 가능 |
| v10 | 2026-02-06 | Sisyphus | **Import Excel 버그 수정** - Nickname Column 추가, 변수 scope 수정, None 처리 |
| v11 | 2026-02-07 | Sisyphus | **Reset Password 변경** - 관리자 비밀번호 초기화 시 12345678로 설정 |

---

## v11 (2026-02-07) - Reset Password 변경

---

# 🚀 oaisstart run 워크플로우 가이드

## 시작하기 전 필수 수행 사항

### 1단계: DEVELOPMENT_LOG.md 읽기 (최우선)
```
DEVELOPMENT_LOG.md를 먼저 읽으시오.
여기에 모든 작업 이력이 기록되어 있소.
여기서부터 이어서 작업하시오.
```

### 2단계: 모든 MD 파일 읽기
```
프로젝트 루트 및 dice_app/ 디렉토리의 모든 .md 파일을 읽으시오:
- *.md (루트)
- dice_app/*.md
- doc/*.md
```

### 3단계: 현재 프로젝트 상태 점검
```
1. Git 상태 확인: git status
2. 마지막 커밋 확인: git log --oneline -5
3. 작업 중인 브랜치 확인
4. 로컬 변경사항 확인
```

### 4단계: 작업 준비 완료
```
위 단계를 모두 수행한 후에만 코드 작업을 시작하시오.
DEVELOPMENT_LOG.md에 기록된 내용을 기준으로 현재 상태를 파악하시오.
```

## 기록 규칙

### 기록 위치: DEVELOPMENT_LOG.md만 사용
- **다른 MD 파일에는 기록하지 마시오**
- **모든 변경사항은 DEVELOPMENT_LOG.md에만 기록하시오**
- 코드 수정이 완료되면 즉시 기록하시오

### 기록 형식
```
1. 섹션 번호는 계속 증가 (#1, #2, #3...)
2. "문서 이력" 테이블에 버전 추가
3. 해당 섹션에 상세 내용 기록
4. 커밋 메시지와 연결
```

### 커밋/푸시 시
```
1. 코드 변경 완료
2. DEVELOPMENT_LOG.md에 기록
3. Git 커밋 (bland7754 계정)
4. Git 푸시
5. Streamlit Cloud에서 Rebuild
```

## ⚠️ 중요 규칙

| ❌ 금지 | ✅ 허용 |
|---------|---------|
| 다른 MD 파일에 작업 기록 | DEVELOPMENT_LOG.md에만 기록 |
| 기록 없이 코드만 푸시 | 코드 + 로그 함께 기록 |
|.md 파일 덮어쓰기 | DEVELOPMENT_LOG.md에 섹션 추가 |

---

이 문서(D DEVELOPMENT_LOG.md)가 **"여기서부터 이어서"** 문서입니다.
**모든 것은 여기에 기록됩니다.**

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

---

# 12. 비밀번호 변경 기능 (2026-02-05)

## 12.1 개요

사용자와 관리자가 기존 비밀번호로 인증 후 새 비밀번호로 변경할 수 있는 기능 추가.

## 12.2 추가된 파일

| 파일 | 설명 |
|------|------|
| `dice_app/views/change_password.py` | 사용자 비밀번호 변경 페이지 |

## 12.3 수정된 파일

### auth.py 수정
```python
# 새 함수 추가
def change_user_password(user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """사용자 비밀번호 변경 - 기존 비밀번호 인증 후 새 비밀번호로 변경"""

def change_admin_password(admin_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """관리자 비밀번호 변경 - 기존 비밀번호 인증 후 새 비밀번호로 변경"""

# 기존 함수 수정
def logout(): ...
# login 함수: 누락된 return 문 추가 (fallback)
```

### database.py 수정
```python
# 새 함수 추가
def update_user_password(user_id: str, new_password_hash: str) -> bool:
    """사용자 비밀번호 해시 업데이트"""

def update_admin_password(admin_id: str, new_password_hash: str) -> bool:
    """관리자 비밀번호 해시 업데이트"""
```

### app.py 수정
```python
# 일반 사용자 메뉴에 "🔐 Change Password" 추가
page = st.radio(
    "Select Page",
    ["🏠 Home", "📝 Make Reservation", "📊 My Reservations", "🔐 Change Password"],
)

# 라우팅 추가
elif page == "🔐 Change Password":
    import views.change_password
    views.change_password.show()
```

### views/master_admin.py 수정
```python
#管理员页面新增密码修改区域
st.markdown("### 🔐 Change My Password")
# 비밀번호 변경 폼 추가 (기존 비밀번호 확인 + 새 비밀번호)
```

### views/admin_dashboard.py 수정
```python
#管理员操作区新增密码修改链接
col1, col2 = st.columns(2)
with col1:
    if st.button("🔐 Change My Password", use_container_width=True):
        st.session_state["page"] = "admin_management"
        st.rerun()
```

## 12.4 기능 상세

### 사용자 비밀번호 변경 페이지 (`change_password.py`)
- 기존 비밀번호 입력 → 새 비밀번호 입력 → 새 비밀번호 확인
- 검증:
  - 기존 비밀번호 미입력 에러
  - 새 비밀번호 8자 미만 에러
  - 새 비밀번호 불일치 에러
  - 기존 비밀번호와 동일 시 에러
- 성공 시: 로그아웃 후 새 비밀번호로 재로그인 요청

### 관리자 비밀번호 변경 (master_admin.py)
- 마스터/관리자 계정용 비밀번호 변경 섹션
- 동일한 검증 로직 적용
- 마스터管理员页面底部显示

## 12.5 네비게이션

| 사용자 유형 | 접근 경로 |
|------------|-----------|
| 일반 사용자 | 사이드바 Menu → 🔐 Change Password |
| 관리자 | Admin Dashboard → 🔐 Change My Password 버튼 |
| 마스터 | Admin Account Management 페이지 하단 |

## 12.6 보안 사항

- 기존 비밀번호 인증 필수
- 새 비밀번호 최소 8자
- bcrypt 해싱 후 저장
- 비밀번호 변경 후 자동 로그아웃

---

# 13. 이벤트 세션 활성화 버그 수정 (2026-02-05)

## 13.1 문제 증상
- 세션 생성은 성공하지만 활성화가 적용되지 않음
- 활성화/비활성화 버튼 클릭 시 반응 없음
- 이벤트 세션 관리 페이지에서 "No active session" 메시지 계속 표시
- 메인 홈에 예약 상태가 적용되지 않음

## 13.2 원인 분석

### 문제 1: create_session()에서 is_active 미설정
```python
# 기존 코드 - is_active가 새 세션에 설정되지 않음
insert(
    "event_sessions",
    {
        "session_number": session_number,
        "session_name": session_name,
        ...
        # is_active 누락!
    },
)
```

### 문제 2: 불리언 값 형식 불일치
- 스키마: `is_active boolean NOT NULL DEFAULT false`
- 코드: `"is_active": 0` / `"is_active": 1` (정수형)
- PostgREST가 정수형 boolean을 제대로 처리하지 못함

### 문제 3: get_active_session() 쿼리 형식 오류
```python
# 기존 코드
return fetch_one("event_sessions", {"is_active": "eq.1"})
# 올바른 형식
return fetch_one("event_sessions", {"is_active": "eq.true"})
```

## 13.3 수정 내용

### database.py 수정
```python
# create_session() - 새 세션에 is_active: True 추가
insert(
    "event_sessions",
    {
        ...
        "is_active": True,  # 활성 상태로 생성
    },
)

# 기존 세션 비활성화 - 불리언 형식 사용
update("event_sessions", {"is_active": False}, {"is_active": "eq.True"})

# update_session_active() - 불리언 값 직접 전달
return update(
    "event_sessions",
    {"is_active": is_active},  # Python bool을 JSON bool로 변환
    {"id": f"eq.{session_id}"},
)

# get_active_session() - 쿼리 형식 수정
return fetch_one("event_sessions", {"is_active": "eq.true"})
```

## 13.4 테스트 방법
1. 기존 세션 삭제
2. 새 세션 생성
3. 상단에 "Current active session" 메시지 확인
4. 메인 홈에서 예약 상태 변경 확인
5. 활성화/비활성화 버튼 테스트

---

# 14. Participants Management 개선 (2026-02-05)

## 14.1 새로운 기능 개요

### 탭 구조 변경
| 이전 | 이후 |
|------|------|
| Participants List | **Participants List** |
| Add Participant | **Add to Session** |
| Import Excel/CSV | **Import Excel** + 자동 비밀번호 생성 |
| (없음) | **Manage Users** - 생성된 계정 관리 |

## 14.2 Excel 업로드 + ID/비밀번호 자동 생성

### 기능 설명
```python
# Excel 업로드 시:
1. 닉네임, IGG ID, 소속, 연맹 컬럼 매핑
2. 새 참여자: 랜덤 비밀번호 생성 (12자리)
3. 기존 사용자: 기존 계정 사용
4. users 테이블에 계정 생성
5. participants 테이블에 참여자 등록
6. 생성된 Credentials CSV 다운로드
```

### 생성되는 Credentials
| 필드 | 설명 |
|------|------|
| Nickname | Excel에서 가져옴 |
| IGG ID | Excel 값 또는 `DGXXXXXX` 형식으로 자동 생성 |
| Password | 12자리 랜덤 문자열 |
| Status | "New" 또는 "Existing" |

## 14.3 Add to Session 탭 - 일괄 작업

### 기능 1: 세션에 참여자 추가
- 현재 세션에 참여자 일괄 등록
- 체크박스로 선택 가능
- "Select All" 전체 선택

### 기능 2: 예약 명단에 추가
- 세션 참여자를 예약 명단에 추가
- 관리자가 직접 승인된 것으로 처리
- "Pre-registered by admin" 메모 포함

### 상태 구분
| 상태 | 설명 |
|------|------|
| 🎯 This Session | 현재 세션에 등록됨 |
| ⏳ Pending | 세션에 미등록 |
| ✅ Completed | 완료됨 |

## 14.4 Manage Users 탭

- Excel 업로드로 생성된 사용자 계정 조회
- 검색 기능
- 활성화/비활성 상태 확인

## 14.5 사용 워크플로우

### 워크플로우 1: 새 참여자 등록
```
1. Excel 파일 준비 (닉네임, 소속, 연맹)
2. Participants Management → Import Excel
3. 파일 업로드 및 컬럼 매핑
4. 세션 선택
5. Import 클릭
6. 생성된 Credentials CSV 다운로드
7. 참여자에게 ID/비밀번호 배포
```

### 워크플로우 2: 기존 참여자를 이번 세션에 등록
```
1. Participants Management → Add to Session
2. 세션에 미등록 참여자 목록 확인
3. 체크박스로 선택
4. "Add Selected to Session" 클릭
5. 예약 명단에 추가하려면 하단에서 선택 후 "Add Selected to Reservations"
```

## 14.6 상태 표시

### Participants List에서
| 배지 | 의미 |
|------|------|
| 🎯 This Session | 현재 활성화된 세션에 등록됨 |
| ⏳ Pending | 세션에 미등록 |
| ✅ Completed | 완료됨 |

### 예약 명단에서
| 상태 | 의미 |
|------|------|
| Pre-registered | 관리자가 미리 등록 |
| Reservation | 사용자가 직접 신청 |

---

# 15. 관리자 비밀번호 열람 기능 (2026-02-05)

## 15.1 개요

관리자가 참여자에게 배포할 비밀번호를 열람할 수 있는 기능 추가.

## 15.2 데이터베이스 변경

### users 테이블에 plaintext_password 컬럼 추가
```sql
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS plaintext_password text;
```

**SQL 파일**: `.sisyphus/add_plaintext_password.sql`

## 15.3 기능 설명

### 관리자만 접근 가능
- Manage Users 탭은 `auth.require_login(required_role="admin")`로 보호
- 일반 사용자는 비밀번호 열람 불가

### 비밀번호 열람 UI
```
1. Manage Users 탭 이동
2. 사용자 확장 (Expander) 클릭
3. 👁️ 버튼으로 비밀번호 토글
4. 전체 비밀번호 보기는 "Show All Passwords" 체크박스
```

### 비밀번호 재설정
- 관리자가 비밀번호 재설정 가능
- 새 비밀번호 자동 생성 + 저장
- 즉시 열람 가능

## 15.4 Import Excel과 연동

### 새 사용자 등록 시
```python
# users 테이블에 평문 비밀번호 저장
user_data = {
    "commander_number": igg_id,
    "nickname": nickname,
    "password_hash": hash,      # 해시 (인증용)
    "plaintext_password": pw,  # 평문 (관리자 열람용)
    ...
}
```

### 기존 사용자
- 처음 저장된 비밀번호가 없으면 자동 저장
- 이미 있으면 기존 값 유지

## 15.5 Credentials 다운로드

### 개별 다운로드
- Import 완료 시 CSV 다운로드
- Nickname, Commander ID, Password 포함

### 전체 다운로드
- Manage Users 탭에서 "Download All Credentials"
- 모든 사용자의 비밀번호 포함 CSV

## 15.6 보안 고려사항

| 항목 | 설명 |
|------|------|
| 접근 제어 | 관리자만 열람 가능 |
| 저장 방식 | 평문 저장 (RLS 미적용) |
| 용도 | 초기 비밀번호 배포용 |
| 변경 시 | 사용자가 비밀번호 변경 권장 |

## 15.7 사용 워크플로우

```
1. Excel로 참여자 Import
2. Credentials CSV 다운로드
3. 관리자가 Manage Users에서 비밀번호 확인
4. 참여자에게 ID/비밀번호 메시지
5. 참여자 로그인 후 비밀번호 변경
```

---

# 16. Excel Import 형식 지정 (2026-02-05)

## 16.1 Excel 형식 요구사항

### 컬럼 파싱 규칙

| Excel 데이터 | 파싱 결과 |
|-------------|-----------|
| 10자리 숫자 | 사령관 ID로 사용 |
| `#000 연맹이름` | 서버: `#000`, 연맹: `연맹이름` |
| 닉네임 | 빈칸 (사용자 직접 변경) |
| 중복 사령관 ID | 1개만 남김 |

### 예시

| 소속 | 파싱 결과 |
|------|-----------|
| `#12345 GuildName` | 서버: `#12345`, 연맹: `GuildName` |
| `#99999 NoAlliance` | 서버: `#99999`, 연맹: `NoAlliance` |

## 16.2 처리 로직

```python
# 1. 10자리 숫자 추출
match = re.search(r"\d{10}", raw_id)
commander_id = match.group()  # 1234567890

# 2. 소속 파싱 "#000 alliance_name"
parts = raw_aff.split(" ", 1)
server = parts[0]      # #12345
alliance = parts[1]    # GuildName

# 3. 닉네임은 빈칸
nickname = ""

# 4. 중복 제거
seen_commander_ids = set()
```

## 16.3 Import 결과

| 필드 | 값 |
|------|-----|
| commander_id | 1234567890 |
| nickname | (빈칸) |
| server | #12345 |
| alliance | GuildName |
| password | 자동 생성 (12자리) |

## 16.4 Credentials CSV 출력

| Commander ID | Server | Alliance | Password | Status |
|--------------|--------|----------|----------|--------|
| 1234567890 | #12345 | GuildName | xk9sL2mN5pQ | New |
| 0987654321 | #99999 | NoAlliance | aBcDeFgHiJkL | New |

## 16.5 사용 방법

```
1. Excel 파일 준비 (소속 형식: #서버번호 연맹이름)
2. Participants Management → Import Excel
3. Commander ID 컬럼 선택 (10자리 숫자)
4. Affiliation 컬럼 선택 (#000 연맹이름 형식)
5. Preview 확인
6. Import 클릭
7. Credentials CSV 다운로드
8. 참여자에게 배포
```

---

# 17. 세션 삭제 기능 수정 (2026-02-05)

## 17.1 문제

- 세션 삭제 버튼 클릭 시 반응 없음
- 삭제 확인 대화상자 표시되지 않음

## 17.2 원인

- Streamlit의 session_state가 expander 내부에서 초기화되어 상태가 유지되지 않음
- 복잡한 상태 키命名로 인한 혼란

## 17.3 수정 내용

### 함수 상단에서 상태 초기화
```python
def show():
    # 단일 confirm 상태로 관리
    if "delete_confirm_id" not in st.session_state:
        st.session_state["delete_confirm_id"] = None
```

### 간소화된 확인 흐름
```python
if st.session_state.get("delete_confirm_id") == session["id"]:
    # 삭제 확인 대화상자 표시
    if st.button("Yes, Delete"):
        delete_session(session["id"])
else:
    if st.button("Delete"):
        st.session_state["delete_confirm_id"] = session["id"]
```

## 17.4 테스트 결과

```bash
# DELETE API 테스트
Delete Status: 204
Remaining Sessions: []
```

---

# 18. 홈 페이지 예약 상태 수정 (2026-02-05)

## 18.1 문제

- 세션이 활성화되지 않았는데도 홈 페이지에 "예약 접수 중" 표시
- 세션이 없을 때 예약이 가능해야 하는 것으로 오해

## 18.2 원인

```python
# 기존 코드 - 잘못된 로직
else:
    "is_reservation_open": True,  # No session = always open ❌
    "is_reservation_closed": False,
```

## 18.3 수정 내용

### 예약 상태 변경
```python
# 수정 후 - 세션이 없으면 예약 불가
else:
    "is_reservation_open": False,  # No session = reservations not open ✅
    "is_reservation_closed": True,
```

### 홈 페이지 표시
```python
# 세션이 없을 때
st.warning("## 📢 No Active Session")
st.info("Reservations are not available at this time.")
st.markdown("Please wait for an administrator to create and activate a session.")
```

## 18.4 예약 상태표시

| 상태 | 세션활성화 | 예약가능 | 표시메시지 |
|------|-----------|---------|----------|
| 예약가능 | ✅ | ✅ | ✅ Reservations Open |
| 마감임박 | ✅ | ✅ (시간차) | ⏰ Reservations Opening Soon |
| 마감 | ✅ | ❌ | ⛔ Reservations Closed |
| 대기명단 | ✅ | ✅ (가득참) | ⏳ Waitlist Only |
| **세션없음** | ❌ | ❌ | **📢 No Active Session** |

---

# 19. 이벤트 세션 KeyError 수정 (2026-02-05)

## 19.1 문제

```
KeyError: This app has encountered an error.
File "/mount/src/dawn_dice/dice_app/views/event_sessions.py", line 144, in show
    if r["status"] == "pending"
```

## 19.2 원인

- `r["status"]`를 직접 접근하는데 `status` 컬럼이 없음
- Supabase 스키마에서 `status` 컬럼을 제거함

## 19.3 수정 내용

```python
# 수정 전 (에러 발생)
pending = len([r for r in session_reservations if r["status"] == "pending"])

# 수정 후 (.get() 사용)
pending = 0
approved = 0
waitlisted = 0

for r in session_reservations:
    status = r.get("status") or ""
    if status == "pending":
        pending += 1
    elif status == "approved":
        approved += 1
    elif status == "waitlisted":
        waitlisted += 1
```

## 19.4 테스트 결과

- 에러 없이 세션 관리 페이지 로드 ✅
- 예약 카운트 표시 정상 작동

---

# 20. 관리자 설정 및 공개 페이지 영어 전환 (2026-02-05)

## 20.1 문제

- `admin_reservation_settings.py` 한글로 표시
- `public_status.py` 한글로 표시

## 20.2 수정된 파일

| 파일 | 변경 사항 |
|------|----------|
| `dice_app/views/admin_reservation_settings.py` | 전체 UI 영어로 변경 |
| `dice_app/views/public_status.py` | 전체 UI 영어로 변경 |

## 20.3 주요 변경 항목

### admin_reservation_settings.py
| 이전 | 이후 |
|------|------|
| 예약 설정 관리 | Reservation Settings |
| 예약 오픈됨/마감됨 | Reservations are OPEN/CLOSED |
| 예약 오픈 시간/마감 시간 | Reservation Open/Close Time |
| 승인됨/대기 중/대기자/거절됨 | Approved/Pending/Waitlist/Rejected |
| 정원이 초과되었습니다! | Capacity exceeded! |

### public_status.py
| 이전 | 이후 |
|------|------|
| 예약 현황 - DaWn Dice Party | Reservation Status - DaWn Dice Party |
| 예약이 가능합니다! | Reservations are OPEN! |
| 예약 방법 | How to Reserve |
| 남은 자리 | Remaining Spots |
approved = 0
waitlisted = 0

for r in session_reservations:
    status = r.get("status") or ""
    if status == "pending":
        pending += 1
    elif status == "approved":
        approved += 1
    elif status == "waitlisted":
        waitlisted += 1
```

## 19.4 테스트 결과

- 에러 없이 세션 관리 페이지 로드 ✅
- 예약 카운트 표시 정상 작동

---

# 20. 세션 Created By 표시 수정 (2026-02-05)

## 20.1 문제

```
**Created By**: {session.get("creator_name", "Unknown")}
```

`creator_name` 컬럼이 존재하지 않아 항상 "Unknown" 표시

## 20.2 원인

- `event_sessions` 테이블에 `creator_name` 컬럼 없음
- `created_by`에는 사용자 ID만 저장됨

## 20.3 수정 내용

```python
# 수정 전
**Created By**: {session.get("creator_name", "Unknown")}

# 수정 후 - created_by ID로 사용자 정보 조회
created_by = session.get("created_by", "")
creator_name = "Unknown"
if created_by:
    admin = db.get_admin_by_id(created_by)
    if admin:
        creator_name = admin.get("nickname") or admin.get("username", "Unknown")
    else:
        user = db.get_user_by_id(created_by)
        if user:
            creator_name = user.get("nickname", "Unknown")
```

## 20.4 결과

- 세션 생성자 이름이 올바르게 표시됨
- 관리자와 일반 사용자 모두 지원


---

# 21. Import Excel 버그 수정 (2026-02-06)

## 21.1 수정 목록

| 날짜 | 커밋 | 수정 내용 | 비고 |
|------|------|----------|------|
| 2026-02-06 | 240fe79 | `participant.get("number")` None 처리 | `int(None)` 에러 방지 |
| 2026-02-06 | 3555d9c | DEBUG 코드 제거 | |
| 2026-02-06 | cea0f9b | Nickname Column 추가 | Column Mapping 3개로 확장 |
| 2026-02-06 | e27d330 | nickname 변수 scope 수정 | 기존 사용자 없을 때 undefined 문제 |
| 2026-02-06 | bdd37db | session_state 처리 수정 | `st.session_state.get()` 사용 |

## 21.2 상세 내용

### 21.2.1 Nickname Column 추가 (cea0f9b)

**문제:** Excel에서 닉네임 열을 선택할 수 없어서 정보 손실

**수정 전:**
```
Column Mapping: 2개 (Commander ID, Affiliation)
```

**수정 후:**
```
Column Mapping: 3개 (Commander ID, Nickname, Affiliation)
```

**사용 방법:**
1. Commander ID Column: `IGG아이디` 선택
2. **Nickname Column**: 닉네임 열 선택 (새로 추가)
3. Affiliation Column: `소속` 선택

### 21.2.2 nickname 변수 scope 수정 (e27d330)

**문제:** 기존 사용자가 없을 때 `nickname` 변수가 정의되지 않음

**에러 메시지:**
```
cannot access local variable 'nickname' where it is not associated with a value
```

**수정:**
```python
# 수정 전
else:
    user_data = {
        "nickname": nickname if nickname else "",  # nickname 미정의
    }
    ...
    nickname = ""  # 정의가 나중에!

# 수정 후
else:
    user_data = {
        "nickname": data.get("nickname", ""),  # data에서 직접 가져옴
    }
```

### 21.2.3 participant.number None 처리 (240fe79)

**문제:** Participants 편집 시 `number` 필드가 None이면 에러

**에러:**
```
TypeError: int(None) - cannot convert None to int
```

**수정:**
```python
# 수정 전
value=int(participant.get("number", 1))

# 수정 후
value=int(participant.get("number") or 1)
```

### 21.2.4 session_state 처리 수정 (bdd37db)

**문제:** `st.selectbox`의 `key`로 저장된 값을 직접 참조하여 에러

**수정:**
```python
# 수정 전
if import_session_id == "Select Session...":

# 수정 후
selected_session_id = st.session_state.get("import_session_id", "Select Session...")
if selected_session_id == "Select Session...":
```

## 21.3 사용된 GitHub 계정

| 작업 | 계정 |
|------|------|
| 커밋/푸시 | `bland7754` |

---

*DEVELOPMENT_LOG.md - DaWn Dice Party 개발 이력*
