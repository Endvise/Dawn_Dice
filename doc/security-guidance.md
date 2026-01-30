# security-guidance - 보안 가이드라인 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | security-guidance |
| 역할 | 보안 가이드라인 제공 |
| 제공자 | claude-plugins-official |

코드 보안 취약점 분석 및 보안 모범 사례를 제공하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install security-guidance@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 취약점 스캔 | OWASP Top 10 기반 취약점 탐지 |
| 보안 리뷰 | 코드 보안 검토 및 권고 |
| 의존성 검사 | 취약한 패키지 의존성 탐지 |
| 시크릿 탐지 | 하드코딩된 비밀 정보 탐지 |
| 보안 가이드 | 언어/프레임워크별 보안 가이드 |

---

## 4. 사용법

### 4.1 보안 스캔

```bash
# 프로젝트 보안 스캔
/security-guidance scan

# 특정 파일 스캔
/security-guidance scan src/auth.py
```

### 4.2 의존성 검사

```bash
# 취약한 의존성 검사
/security-guidance audit
```

---

## 5. 탐지 취약점 유형

| 취약점 | 설명 |
|--------|------|
| SQL Injection | SQL 인젝션 취약점 |
| XSS | 크로스 사이트 스크립팅 |
| CSRF | 크로스 사이트 요청 위조 |
| Path Traversal | 경로 탐색 취약점 |
| Hardcoded Secrets | 하드코딩된 비밀 정보 |
| Insecure Deserialization | 안전하지 않은 역직렬화 |

---

## 6. OWASP Top 10 커버리지

| 순위 | 취약점 | 지원 |
|------|--------|------|
| A01 | Broken Access Control | O |
| A02 | Cryptographic Failures | O |
| A03 | Injection | O |
| A04 | Insecure Design | Partial |
| A05 | Security Misconfiguration | O |
| A06 | Vulnerable Components | O |
| A07 | Authentication Failures | O |
| A08 | Software Integrity Failures | Partial |
| A09 | Logging Failures | Partial |
| A10 | SSRF | O |

---

## 7. 관련 문서

- `doc/code-review.md` - PR/코드 리뷰 자동화 플러그인
- `v/oaischeck.md` - 코드 품질 체크 스킬
- `.claude/PRINCIPLES.md` - 보안 모범 사례 섹션
