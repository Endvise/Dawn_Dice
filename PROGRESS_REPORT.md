# DaWn Dice Party - 개발 진행 보고서

## 문서 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v01 | 2026-02-03 | Sisyphus | 초기 작성 - Supabase 연동 문제 분석 |
| v02 | 2026-02-03 | Sisyphus | 진행 상황 및 이슈 정리 |
| v03 | 2026-02-03 | Sisyphus | 보안 강화 - .secrets/ 디렉토리 이동 |

---

## 1. 완료된 작업

### Phase 2: 코드 리팩토링 ✅

| 파일 | 작업 내용 | 상태 |
|------|----------|------|
| `dice_app/config.py` | **신규 생성** - Supabase/설정 중앙化管理 | ✅ 완료 |
| `dice_app/database.py` | `config.py` 사용, `commander_id` 수정 | ✅ 완료 |
| `dice_app/auth.py` | `config.py` 사용, Supabase Auth 로직 간소화 | ✅ 완료 |

### Phase 3: 신규 기능 구현 ✅

| 파일 | 기능 | 상태 |
|------|------|------|
| `dice_app/views/public_status.py` | 외부인 예약 현황 공개 UI | ✅ 완료 |
| `dice_app/utils/excel_uploader.py` | Excel/CSV → Supabase 자동 업로드 | ✅ 완료 |
| `dice_app/utils/excel_uploader.py` | Google Sheets 블랙리스트 동기화 | ✅ 완료 |
| `dice_app/views/admin_reservation_settings.py` | 관리자 예약 설정 페이지 | ✅ 완료 |

### Phase 4: 스키마 수정 ✅

| 파일 | 수정 내용 | 상태 |
|------|----------|------|
| 전체 파일 | `commander_number` → `commander_id` | ✅ 완료 |

---

## 2. 보안 강화 완료 🔒

### 2.1 Secrets 파일 분리

**이전 (위험):**
```
.streamlit/secrets.toml  ← Git에 포함될 위험
```

**이후 (안전):**
```
.secrets/supabase_secrets.toml  ← .gitignore에 포함됨 (Git 추적 안됨)
.streamlit/secrets.toml  ← 템플릿만 존재 (실제 키 없음)
```

### 2.2 .gitignore 업데이트

```gitignore
# Supabase keys - NEVER commit!
.secrets/
*secrets*
*service_role*
sb_*
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9*
```

### 2.3 config.py 업데이트

```python
# secrets 파일 경로 우선순위
SECRETS_PATHS = [
    Path(".secrets/supabase_secrets.toml"),  # 최우선 (gitignored)
    Path(".streamlit/secrets.toml"),  # Streamlit 기본
]
```

---

## 3. Supabase 테스트 결과

### 3.1 연결 테스트

```
=== Supabase Connection Test ===
[1] GET test (users)... - Status: 200 ✓
[2] INSERT test - Status: 400 ✗
```

**결과:**
- GET (읽기): 성공
- INSERT (쓰기): 실패 (스키마 불일치)

### 3.2 발견된 문제

| 항목 | 상태 |
|------|------|
| service_role key | ✅ 설정됨 |
| users 테이블 존재 | ✅ 존재 |
| users 테이블 데이터 | ❌ 없음 (0개) |
| reservations 테이블 | ✅ 존재 (빈 테이블) |
| blacklist 테이블 | ✅ 존재 (빈 테이블) |
| participants 테이블 | ❌ 없음 (404) |
| announcements 테이블 | ❌ 없음 (404) |

### 3.3 스키마 불일치

**코드에서 사용하는 컬럼:**
```python
'username', 'commander_id', 'password_hash', 'role', ...
```

**실제 테이블 (불일치):**
- `username` 컬럼 없음
- `commander_id` 컬럼 없음
- 실제 컬럼명 미확인

---

## 4. 다음 작업

### 4.1 Supabase Dashboard에서 필요한 작업

1. **테이블 생성/스키마 확인**
   - `users`, `reservations`, `blacklist` 테이블 구조 확인
   - `participants`, `announcements` 테이블 생성 (필요시)

2. **컬럼명 확인**
   - 현재 코드: `username`, `commander_id`, `role` 등
   - 실제 컬럼명 확인 필요

### 4.2 코드에서 수정 필요

**컬럼명이 다를 경우:**
```python
# 현재 코드
"commander_id": "ABC123"

# 실제 컬럼명이 'commander_number'라면
"commander_number": "ABC123"
```

---

## 5. 파일 목록

### 5.1 생성된 파일

| 파일 | 용도 | Git 추적 |
|------|------|----------|
| `dice_app/config.py` | 설정 중앙화 | ✅ |
| `dice_app/views/public_status.py` | 예약 현황 공개 UI | ✅ |
| `dice_app/utils/excel_uploader.py` | Excel 업로드 + 동기화 | ✅ |
| `dice_app/views/admin_reservation_settings.py` | 관리자 예약 설정 | ✅ |
| `oaisplan.md` | 전체 개발 계획서 | ✅ |
| `PROGRESS_REPORT.md` | 진행 상황 보고서 | ✅ |
| `test_supabase_connection.py` | 연결 테스트 스크립트 | ✅ |

### 5.2 보안 관련 파일 (Git 추적 안됨)

| 파일 | 용도 |
|------|------|
| `.secrets/supabase_secrets.toml` | **실제 API 키** - Git 추적 안됨 |

### 5.3 템플릿 파일

| 파일 | 용도 |
|------|------|
| `.streamlit/secrets.toml` | 템플릿 (실제 키 없음) |

---

## 6. 체크리스트

### 6.1 보안 설정 ✅

- [x] `.secrets/` 디렉토리 생성
- [x] `supabase_secrets.toml` 이동
- [x] `.gitignore` 업데이트
- [x] `.streamlit/secrets.toml` 템플릿화

### 6.2 Supabase 연동

- [ ] Dashboard에서 실제 스키마 확인
- [ ] 코드와 스키마 일치시키기
- [ ] INSERT 테스트 통과 확인
- [ ] 마스터 계정 생성 테스트

---

## 7. 참조 URL

- Supabase Dashboard: https://supabase.com/dashboard/project/gticuuzplbemivfturuz
- 프로젝트 문서: `oaisplan.md`, `PROGRESS_REPORT.md`

---

*본 보고서는 2026-02-03에 업데이트되었습니다.*

**문제점:**
- `SUPABASE_KEY`는 **anon key (publishable key)**로 읽기 전용
- INSERT/UPDATE/DELETE 작업 시 401 Unauthorized 에러 발생

**해결책:**
```
1. Supabase Dashboard 접속
2. Settings → API → service_role 섹션
3. service_role key 복사
4. secrets.toml의 SERVICE_ROLE_KEY에 붙여넣기
```

### 3.2 테이블 스키마 불일치

**테스트 결과:**
```
INSERT 테스트:
Status: 400
Response: {"code":"PGRST204","message":"Could not find the 'role' column of 'users' in the schema cache"}
```

**발견된 불일치:**

| 항목 | 코드 (database.py) | DATABASE_SCHEMA.md | 실제 Supabase |
|------|-------------------|-------------------|--------------|
| users | `commander_number` | `commander_id` | ? |
| users | `role` 컬럼 존재 | `role` 존재 | ❌ 없음 |

**가능한 원인:**
1. 실제 Supabase 테이블이 DATABASE_SCHEMA.md와 다름
2. RLS (Row Level Security) 정책이 적용됨
3. 테이블이 생성되지 않음

---

## 4. 다음에 이어서 작업할 내용

### 4.1 즉시 실행해야 할 작업

```bash
# 1. service_role key 설정
# .streamlit/secrets.toml 수정:
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # 실제 key

# 2. Supabase 테이블 스키마 확인
# Dashboard → Table Editor에서 컬럼명 확인

# 3. 스키마 수정 완료
# commander_number → commander_id 로 모든 파일 수정
```

### 4.2 코드 수정 필요한 부분

**commander_number → commander_id 수정 필요 파일:**

```bash
# 수정 대상 파일:
dice_app/database.py
dice_app/auth.py
dice_app/utils/excel_uploader.py
dice_app/views/admin_reservation_settings.py
```

### 4.3 테스트 실행

```bash
# 연결 테스트
python test_supabase_connection.py

# 또는 직접 테스트
python -c "
import requests
url = 'https://gticuuzplbemivfturuz.supabase.co'
key = 'your_service_role_key'
headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

# GET 테스트
r = requests.get(f'{url}/rest/v1/users?select=*&limit=1', headers=headers)
print(f'GET Status: {r.status_code}')

# INSERT 테스트
data = {'username': 'test', 'commander_id': 'TEST123', 'password_hash': 'hash', 'role': 'user'}
r = requests.post(f'{url}/rest/v1/users', headers=headers, json=data)
print(f'INSERT Status: {r.status_code}')
"
```

---

## 5. 현재 코드 상태 요약

### 5.1 새로 생성한 파일

| 파일 | 용도 |
|------|------|
| `dice_app/config.py` | 설정 중앙化管理 |
| `dice_app/views/public_status.py` | 예약 현황 공개 페이지 |
| `dice_app/utils/excel_uploader.py` | Excel 업로드 + 블랙리스트 동기화 |
| `dice_app/views/admin_reservation_settings.py` | 관리자 예약 설정 |
| `test_supabase_connection.py` | 연결 테스트 스크립트 |
| `oaisplan.md` | 전체 개발 계획서 |

### 5.2 수정한 파일

| 파일 | 수정 내용 |
|------|----------|
| `dice_app/database.py` | config.py 연동, commander_number → commander_id (진행 중) |
| `dice_app/auth.py` | config.py 연동, 인증 로직 간소화 |
| `.streamlit/secrets.toml` | SERVICE_ROLE_KEY 필드 추가 |

---

## 6. 알려진 이슈

### 6.1 LSP 에러 (basedpyright 미설치)

**현상:**
```
ERROR: Import "supabase" could not be resolved
ERROR: commander_number is not defined
```

**원인:**
- basedpyright (Python LSP)가 설치되지 않음
- 실시간语法检查 불가

**영향:**
- 코드 수정 시 실시간 에러 표시
- 실제 실행에는 영향 없음

**해결:**
```bash
pip install basedpyright
```

### 6.2 Supabase 스키마 불확실성

**현재 확인된 정보:**
- DATABASE_SCHEMA.md에는 `commander_id`로 정의
- 코드에서는 `commander_number` 사용
- 실제 Supabase 테이블 컬럼명 미확인

**대응:**
- DATABASE_SCHEMA.md 기준으로 `commander_id`로 통일
- 실제 불일치 시 Dashboard에서 컬럼명 확인 후 수정

---

## 7. 참조 URL

### 7.1 Supabase
- Dashboard: https://supabase.com/dashboard
- 프로젝트: https://supabase.com/dashboard/project/gticuuzplbemivfturuz
- 문서: https://supabase.com/docs

### 7.2 프로젝트 문서
- 구현 계획: `dice_app/IMPLEMENTATION_PLAN.md`
- DB 스키마: `dice_app/DATABASE_SCHEMA.md`
- 보안 가이드: `dice_app/SECURITY_GUIDE.md`
- 개발 계획: `oaisplan.md`

---

## 8. 체크리스트

### 8.1 service_role key 설정
- [ ] Supabase Dashboard 접속
- [ ] Settings → API → service_role key 복사
- [ ] secrets.toml에 SERVICE_ROLE_KEY 설정
- [ ] 연결 테스트 실행

### 8.2 스키마 확인 및 수정
- [ ] Dashboard에서 실제 테이블 컬럼명 확인
- [ ] 코드와 불일치 시 수정
- [ ] INSERT 테스트 통과 확인

### 8.3 전체 테스트
- [ ] 마스터 계정 로그인
- [ ] 사용자 회원가입
- [ ] 예약 신청/취소
- [ ] 블랙리스트 차단 테스트

---

*본 보고서는 2026-02-03에 작성되었습니다.*
*다음 작업자는 위 내용을 참고하여 작업을 이어 주세요.*

---

## 9. 2026-02-06 Import Excel 버그 수정

### 9.1 수정 목록

| 날짜 | 커밋 | 수정 내용 | 비고 |
|------|------|----------|------|
| 2026-02-06 | 240fe79 | `participant.get("number")` None 처리 | `int(None)` 에러 방지 |
| 2026-02-06 | 3555d9c | DEBUG 코드 제거 | |
| 2026-02-06 | cea0f9b | Nickname Column 추가 | Column Mapping 3개로 확장 |
| 2026-02-06 | e27d330 | nickname 변수 scope 수정 | 기존 사용자 없을 때 undefined 문제 |
| 2026-02-06 | bdd37db | session_state 처리 수정 | `st.session_state.get()` 사용 |

### 9.2 상세 내용

#### 9.2.1 Nickname Column 추가 (cea0f9b)

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

#### 9.2.2 nickname 변수 scope 수정 (e27d330)

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

#### 9.2.3 participant.number None 처리 (240fe79)

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

### 9.3 사용 중인 GitHub 계정

| 작업 | 계정 |
|------|------|
| 커밋/푸시 | `bland7754` |

---

*본 보고서는 2026-02-06에 업데이트되었습니다.*
