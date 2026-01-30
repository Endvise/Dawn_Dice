# playwright - E2E 테스트 자동화 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | playwright |
| 역할 | E2E 테스트 자동화 |
| 제공자 | claude-plugins-official |

Playwright 기반의 End-to-End 테스트 및 브라우저 자동화를 지원하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install playwright@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| E2E 테스트 | 사용자 시나리오 기반 테스트 |
| 크로스 브라우저 | Chrome, Firefox, Safari, Edge 지원 |
| 스크린샷 | 페이지 캡처 및 비교 |
| 네트워크 모니터링 | API 요청/응답 추적 |
| 성능 측정 | Core Web Vitals 측정 |

---

## 4. 사용법

### 4.1 테스트 실행

```bash
# E2E 테스트 실행
/playwright test

# 특정 테스트 파일 실행
/playwright test tests/login.spec.ts
```

### 4.2 브라우저 자동화

```bash
# 페이지 스크린샷
/playwright screenshot https://example.com

# 페이지 상호작용
/playwright interact "click login button"
```

---

## 5. MCP 도구 목록

| 도구 | 설명 |
|------|------|
| browser_navigate | 페이지 이동 |
| browser_click | 요소 클릭 |
| browser_fill | 입력 필드 채우기 |
| browser_screenshot | 스크린샷 캡처 |
| browser_evaluate | JavaScript 실행 |

---

## 6. 지원 브라우저

| 브라우저 | 상태 |
|---------|------|
| Chromium | Full |
| Firefox | Full |
| WebKit (Safari) | Full |
| Edge | Full |

---

## 7. 관련 문서

- `v/oaistest.md` - 테스트 스킬
- `v/agent/oais-web-test-orchestrator.md` - 웹 테스트 오케스트레이터 에이전트
- `d0003_test.md` - 테스트 시나리오 가이드라인
