# 주사위 예약 시스템 - 보안 가이드

## 📋 개요

이 문서는 주사위 예약 시스템의 보안 대책과 구현 방법을 설명합니다.

---

## 🔒 보안 층 (Security Layers)

### Layer 1: 인증 및 계정 보안

#### 1.1 비밀번호 정책
- **최소 길이**: 8자 이상
- **해싱 알고리즘**: bcrypt (12 rounds)
- **저장 방식**: 해시된 비밀번호만 저장 (평문 미저장)

```python
# database.py
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=st.secrets.get("PASSWORD_HASH_ROUNDS", 12))
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
```

#### 1.2 로그인 실패 제한
- **최대 실패 횟수**: 5회
- **실패 초과 시**: 계정 잠금 + "관리자에게 연락하세요" 메시지

```python
# auth.py
max_attempts = st.secrets.get("MAX_LOGIN_ATTEMPTS", 5)
if user.get('failed_attempts', 0) >= max_attempts:
    return False, "로그인 실패 횟수를 초과했습니다. 관리자에게 연락하세요."
```

#### 1.3 세션 관리
- **세션 타임아웃**: 60분 (default)
- **자동 로그아웃**: 타임아웃 시 강제 로그아웃

```python
# auth.py
timeout_minutes = st.secrets.get("SESSION_TIMEOUT_MINUTES", 60)
if (datetime.now() - login_time) > timedelta(minutes=timeout_minutes):
    logout()
    return False
```

#### 1.4 사령관번호 검증
- **자릿수**: 정확히 10자리
- **형식**: 숫자만 허용
- **중복 체크**: 이미 등록된 번호 거부
- **블랙리스트**: 등록된 번호 차단

```python
# register.py
if len(commander_id) != 10:
    return False, "사령관번호는 10자리여야 합니다."

if not commander_id.isdigit():
    return False, "사령관번호는 숫자로만 구성되어야 합니다."
```

---

### Layer 2: 입력 유효성 검사 (Input Validation)

#### 2.1 사령관번호
- ✅ 10자리 숫자만 허용
- ✅ 중복 체크
- ✅ 블랙리스트 체크

#### 2.2 비밀번호
- ✅ 최소 8자
- ✅ 확인용 비밀번호와 일치 여부 체크

#### 2.3 닉네임
- ✅ 공백 제거
- ✅ XSS 방지 (Streamlit 자동 처리)

#### 2.4 서버/연맹
- ✅ 자유롭게 입력 가능
- ✅ 관리자가 수정 가능
- ⚠️ SQL Injection 방지 (parameterized query 사용)

---

### Layer 3: SQL Injection 방지

모든 데이터베이스 쿼리는 **parameterized query**를 사용합니다.

```python
# ✅ 올바른 방법 (parameterized query)
execute_query(
    "SELECT * FROM users WHERE username = ?",
    (username,),
    fetch="one"
)

# ❌ 위험한 방법 (SQL Injection 취약)
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

---

### Layer 4: Brute Force 방지 (Rate Limiting)

#### 4.1 로그인 시도 제한
- **IP 기반 제한**: 구현 필요
- **계정 기반 제한**: 5회 실패 후 잠금

#### 4.2 Rate Limiter 구현 (권장)
```python
# security.py (추가 예정)
from functools import wraps
from datetime import datetime, timedelta
import streamlit as st

class RateLimiter:
    def __init__(self, max_attempts: int, period_minutes: int):
        self.max_attempts = max_attempts
        self.period = timedelta(minutes=period_minutes)

    def check_rate_limit(self, key: str) -> tuple[bool, str]:
        """Rate limit 체크"""
        now = datetime.now()
        key_time = f"rate_limit_{key}_time"
        key_count = f"rate_limit_{key}_count"

        # 시간 체크
        if key_time in st.session_state:
            elapsed = now - st.session_state[key_time]
            if elapsed > self.period:
                # 기간 지남: 카운터 초기화
                st.session_state[key_count] = 0
                st.session_state[key_time] = now

        # 카운트 체크
        count = st.session_state.get(key_count, 0)
        if count >= self.max_attempts:
            return False, "너무 많은 요청이 있습니다. 잠시 후 다시 시도하세요."

        return True, ""

    def increment(self, key: str):
        """카운터 증가"""
        key_time = f"rate_limit_{key}_time"
        key_count = f"rate_limit_{key}_count"

        if key_time not in st.session_state:
            from datetime import datetime
            st.session_state[key_time] = datetime.now()

        st.session_state[key_count] = st.session_state.get(key_count, 0) + 1
```

---

### Layer 5: Secrets Management

#### 5.1 Streamlit Cloud Secrets
- 모든 비밀 정보는 `st.secrets[]`로 접근
- Git 코드에는 "이름표"만 남음
- 실제 비밀번호는 Streamlit Cloud 서버에 저장

```toml
# .streamlit/secrets.toml (Git에 커밋하지 않음!)
MASTER_USERNAME = "DaWnntt0623"
MASTER_PASSWORD = "4425endvise9897!"
BLACKLIST_GOOGLE_SHEET_URL = "https://..."
```

```python
# 코드에서 사용
master_username = st.secrets.get("MASTER_USERNAME", "default")
```

#### 5.2 .gitignore 설정
```
# .gitignore
.streamlit/secrets.toml
```

---

### Layer 6: 로깅 및 감사 (Logging & Auditing)

#### 6.1 중요 이벤트 로깅
- ✅ 로그인 성공/실패
- ✅ 계정 잠금
- ✅ 예약 신청/승인/거부
- ✅ 블랙리스트 추가/제거
- ✅ 관리자 계정 생성/삭제

#### 6.2 보안 이벤트 모니터링
- 다수의 실패한 로그인 시도
- 의심스러운 패턴 감지
- 관리자 계정 접근 시도

---

### Layer 7: 권한 관리 (RBAC)

#### 7.1 역할 정의
| 역할 | 권한 |
|------|------|
| **master** | 모든 권한 + 관리자 계정 생성/삭제 |
| **admin** | 예약 관리, 블랙리스트, 참여자 관리 |
| **user** | 예약 신청, 내 예약 조회 |

#### 7.2 권한 검증
```python
# auth.py
def is_master() -> bool:
    return get_current_role() == 'master'

def is_admin() -> bool:
    return get_current_role() in ['master', 'admin']

def require_login(required_role: Optional[str] = None):
    """권한이 없으면 접근 차단"""
    if required_role == 'master' and not is_master():
        st.error("마스터 권한이 필요합니다.")
        st.stop()
```

---

### Layer 8: 마스터 계정 보안 강화

#### 8.1 마스터 계정 접근 제한
- ✅ 일반 사용자 접근 불가
- ✅ IP 제한 (Streamlit Cloud에서 설정 가능)
- ✅ 2FA 도입 권장

#### 8.2 마스터 비밀번호 관리
- ✅ 복잡성 요구 (특수문자 포함)
- ✅ 주기적 변경 권장
- ✅ 안전한 비밀번호 관리자 사용

---

### Layer 9: 블랙리스트 통합

#### 9.1 이중 블랙리스트 시스템
- **로컬 블랙리스트**: DB에 저장된 블랙리스트
- **Google Sheets 블랙리스트**: 외부 공유 목록

#### 9.2 자동 블랙리스트 체크
```python
# database.py
def check_blacklist(commander_id: str) -> Optional[Dict[str, Any]]:
    # 1. 로컬 블랙리스트 체크
    result = execute_query("SELECT * FROM blacklist WHERE commander_id = ? ...")

    if result:
        return dict(result)

    # 2. Google Sheets 블랙리스트 체크
    try:
        import requests
        sheet_url = st.secrets.get("BLACKLIST_GOOGLE_SHEET_URL")
        response = requests.get(sheet_url)
        # ... CSV 파싱 및 사령관번호 확인
    except Exception as e:
        st.warning(f"Google Sheets 블랙리스트 조회 실패: {e}")
```

---

## 🛡️ 공격 시나리오별 대응

### 1. Brute Force Attack (무차별 대입 공격)

**대응책:**
- ✅ 로그인 5회 실패 후 계정 잠금
- ✅ 실패 횟수 추적
- ⚠️ Rate Limiting (추후 구현 예정)
- ⚠️ CAPTCHA 도입 (추후 고려)

**메시지:**
> "로그인 실패 횟수를 초과했습니다. 관리자에게 연락하세요."

---

### 2. SQL Injection Attack

**대응책:**
- ✅ 모든 쿼리는 parameterized query 사용
- ✅ 입력값 검증 (사령관번호 10자리 숫자)

---

### 3. XSS (Cross-Site Scripting)

**대응책:**
- ✅ Streamlit 자동 XSS 필터링
- ✅ 사용자 입력은 항상 이스케이프 처리

---

### 4. Session Hijacking (세션 탈취)

**대응책:**
- ✅ 세션 타임아웃 (60분)
- ✅ 비밀번호 변경 시 세션 무효화 (추후 구현)

---

### 5. Dictionary Attack (사전 공격)

**대응책:**
- ✅ bcrypt 해싱 (느린 해싱으로 공격 지연)
- ✅ 복잡한 비밀번호 요구 (8자 이상)

---

### 6. Account Enumeration (계정 열거 공격)

**대응책:**
- ✅ 로그인 실패 시 메시지 통일 ("존재하지 않는 사용자입니다")
- ⚠️ 가입 시 존재하는 계정 여부 노출 방지 (추후 개선)

---

## 📊 보안 체크리스트

### 배포 전 확인
- [ ] `.streamlit/secrets.toml` 파일이 `.gitignore`에 있는지 확인
- [ ] 마스터 비밀번호가 복잡한지 확인
- [ ] Google Sheets URL이 공유 링크인지 확인
- [ ] 데이터베이스 파일이 `.gitignore`에 있는지 확인

### 정기 점검
- [ ] 로그 파일 확인 (의심스러한 활동 체크)
- [ ] 블랙리스트 최신화
- [ ] 마스터 비밀번호 주기적 변경
- [ ] Streamlit Cloud 로그 확인

### 보안 강화 (추후)
- [ ] Rate Limiting 구현
- [ ] CAPTCHA 도입
- [ ] 2FA (이중 인증) 도입
- [ ] IP 화이트리스트 (마스터 계정)
- [ ] 보안 로그 대시보드

---

## 🔧 배포 보안 설정

### Streamlit Cloud 배포 시
1. **Secrets 탭**에서 비밀 정보 입력
2. **Advanced Settings**에서 로그 레벨 설정
3. **Collaborators** 제한 (최소 인원)
4. **Git Repository**를 private으로 유지

### GitHub Repository
1. `.streamlit/secrets.toml` 커밋 방지 (`.gitignore` 확인)
2. `data/` 디렉토리 커밋 방지 (DB 파일 포함)
3. PR을 통한 코드 리뷰 필수
4. 브랜치 보호 규칙 설정

---

## 📞 보안 문제 신고

보안 취약점 발견 시:
1. 즉시 관리자에게 알림
2. 로그 파일 백업
3. 영향 범위 분석
4. 패치 적용
5. 사용자에게 알림 (필요 시)

---

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Streamlit Security](https://docs.streamlit.io/develop/tutorials/privacy-security)
- [Bcrypt Password Hashing](https://pypi.org/project/bcrypt/)
- [SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
