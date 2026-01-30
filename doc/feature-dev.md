# feature-dev - 기능 개발 워크플로우 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | feature-dev |
| 역할 | 기능 개발 워크플로우 |
| 제공자 | claude-plugins-official |

새 기능 개발을 위한 체계적인 워크플로우를 제공하는 플러그인입니다.

---

## 2. 설치

```bash
/plugin install feature-dev@claude-plugins-official
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 기능 계획 | 기능 요구사항 분석 및 계획 수립 |
| 브랜치 관리 | feature 브랜치 생성/관리 |
| 구현 가이드 | 단계별 구현 가이드라인 제공 |
| 테스트 계획 | 테스트 시나리오 자동 생성 |
| PR 준비 | Pull Request 생성 지원 |

---

## 4. 사용법

### 4.1 기능 개발 시작

```bash
# 새 기능 개발 시작
/feature-dev start "사용자 인증 기능"

# 기존 이슈 기반 개발
/feature-dev start --issue #123
```

### 4.2 기능 완료

```bash
# 기능 개발 완료 및 PR 준비
/feature-dev complete
```

---

## 5. 워크플로우

```
1. 기능 계획 수립
     ↓
2. feature 브랜치 생성
     ↓
3. 구현 (단계별 커밋)
     ↓
4. 테스트 작성/실행
     ↓
5. PR 생성 및 리뷰 요청
```

---

## 6. 관련 문서

- `doc/code-review.md` - PR/코드 리뷰 자동화 플러그인
- `doc/commit-commands.md` - Git 커밋 메시지 생성 플러그인
- `v/oaisdev.md` - 개발 스킬
