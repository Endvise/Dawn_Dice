# serena - 심볼릭 코드 분석/편집 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | serena |
| 역할 | 심볼릭 코드 분석/편집 |
| 제공자 | claude-plugins-official |

AST(Abstract Syntax Tree) 기반의 심볼릭 코드 분석 및 리팩토링을 지원하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install serena@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 심볼 검색 | 함수, 클래스, 변수 심볼 검색 |
| 참조 분석 | 심볼 사용처 추적 |
| 리팩토링 | 심볼 이름 변경, 추출, 이동 |
| 코드 네비게이션 | 정의로 이동, 참조 찾기 |
| 의존성 분석 | 모듈/패키지 의존성 시각화 |

---

## 4. 사용법

### 4.1 심볼 검색

```bash
# 함수 심볼 검색
mcp__serena__find_symbol("process_data")

# 클래스 심볼 검색
mcp__serena__find_symbol("UserService")
```

### 4.2 심볼 수정

```bash
# 함수 본문 교체
mcp__serena__replace_symbol_body("old_function", "new_code")
```

### 4.3 코드 구조 분석

```bash
# 프로젝트 심볼 개요
mcp__serena__get_symbols_overview()
```

---

## 5. MCP 도구 목록

| 도구 | 설명 |
|------|------|
| find_symbol | 심볼 검색 |
| get_symbol_references | 참조 찾기 |
| replace_symbol_body | 심볼 본문 교체 |
| rename_symbol | 심볼 이름 변경 |
| get_symbols_overview | 심볼 구조 개요 |

---

## 6. 지원 언어

| 언어 | 지원 수준 |
|------|----------|
| Python | Full |
| JavaScript/TypeScript | Full |
| Java | Partial |
| Go | Partial |

---

## 7. 관련 문서

- `v/oaischeck.md` - 코드 품질 체크 스킬
- `v/oaisfix.md` - 오류 수정 스킬
- `CLAUDE.md` - Serena MCP 심볼릭 분석 섹션
