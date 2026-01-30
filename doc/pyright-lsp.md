# pyright-lsp - Python 타입 체크 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | pyright-lsp |
| 역할 | Python 타입 체크 (Pyright) |
| 제공자 | claude-plugins-official |

Pyright 기반의 Python 정적 타입 체크 및 언어 서버 기능을 제공하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install pyright-lsp@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 타입 체크 | Python 타입 힌트 검증 |
| 자동 완성 | 타입 기반 코드 자동 완성 |
| 타입 추론 | 변수/함수 타입 자동 추론 |
| 오류 진단 | 타입 오류 및 경고 표시 |
| 호버 정보 | 심볼 타입 정보 표시 |

---

## 4. 사용법

### 4.1 타입 체크

```bash
# 프로젝트 타입 체크
/pyright-lsp check

# 특정 파일 타입 체크
/pyright-lsp check src/main.py
```

### 4.2 진단 조회

```bash
# 타입 오류 조회
/pyright-lsp diagnostics
```

---

## 5. 타입 체크 모드

| 모드 | 설명 |
|------|------|
| basic | 기본 타입 체크 |
| standard | 표준 타입 체크 (기본값) |
| strict | 엄격한 타입 체크 |
| all | 모든 체크 활성화 |

---

## 6. pyrightconfig.json 설정

```json
{
  "include": ["src"],
  "exclude": ["**/node_modules", "**/__pycache__"],
  "typeCheckingMode": "standard",
  "pythonVersion": "3.11"
}
```

---

## 7. 관련 도구 비교

| 도구 | 속도 | 엄격성 |
|------|------|--------|
| Pyright | 빠름 | 높음 |
| mypy | 보통 | 중간 |
| Pylance | 빠름 | 높음 |

---

## 8. 관련 문서

- `doc/typescript-lsp.md` - TypeScript 언어 서버 플러그인
- `v/oaischeck.md` - 코드 품질 체크 스킬
- `pyproject.toml` - Python 프로젝트 설정
