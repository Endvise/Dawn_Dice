# frontend-design - 프론트엔드 UI/UX 디자인 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | frontend-design |
| 역할 | 프론트엔드 UI/UX 디자인 |
| 제공자 | claude-plugins-official |

프론트엔드 UI 컴포넌트 설계 및 구현을 지원하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install frontend-design@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| UI 컴포넌트 생성 | React, Vue, Angular 컴포넌트 생성 |
| 반응형 디자인 | 모바일/태블릿/데스크톱 대응 |
| 접근성 (a11y) | WCAG 가이드라인 준수 |
| 디자인 시스템 | Tailwind, Bootstrap 등 연동 |
| 스타일링 | CSS, SCSS, Styled-components 지원 |

---

## 4. 사용법

### 4.1 컴포넌트 생성

```bash
# React 컴포넌트 생성
/frontend-design create Button --framework react

# Vue 컴포넌트 생성
/frontend-design create Card --framework vue
```

### 4.2 디자인 리뷰

```bash
# UI 컴포넌트 리뷰
/frontend-design review src/components/
```

---

## 5. 지원 프레임워크

| 프레임워크 | 버전 |
|-----------|------|
| React | 18+ |
| Vue | 3+ |
| Angular | 15+ |
| Svelte | 4+ |

---

## 6. 관련 문서

- `v/agent/frontend-developer.md` - 프론트엔드 개발 에이전트
- `v/agent/web-design-expert.md` - 웹 디자인 전문가 에이전트
