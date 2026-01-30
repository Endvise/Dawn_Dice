# paper-search-tools - 논문 검색 MCP & Skills 플러그인

## 문서 이력 관리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-23 | 초기 작성 |

---

## 1. 개요

| 항목 | 내용 |
|------|------|
| 플러그인명 | paper-search-tools |
| 역할 | 논문 검색 MCP & Skills |
| 제공자 | fcakyon-claude-plugins |
| 마켓플레이스 | fcakyon/claude-codex-settings |

학술 논문 검색 및 분석을 위한 MCP 서버와 스킬을 제공하는 플러그인입니다.

---

## 2. 설치

### 2.1 마켓플레이스 추가 (필수)

```bash
/plugin marketplace add fcakyon/claude-codex-settings
```

### 2.2 플러그인 설치

```bash
/plugin install paper-search-tools@fcakyon-claude-plugins
```

---

## 3. 주요 기능

| 기능 | 설명 |
|------|------|
| 논문 검색 | arXiv, Semantic Scholar 등 논문 검색 |
| 초록 조회 | 논문 초록 및 메타데이터 조회 |
| 인용 분석 | 인용/피인용 관계 분석 |
| 키워드 추출 | 논문 키워드 자동 추출 |
| 관련 논문 추천 | 유사 논문 추천 |

---

## 4. 사용법

### 4.1 논문 검색

```bash
# 키워드로 논문 검색
/paper-search "deep learning object detection"

# 특정 저자 논문 검색
/paper-search --author "Yann LeCun"
```

### 4.2 논문 분석

```bash
# 논문 요약
/paper-search analyze arxiv:2301.00001

# 관련 논문 찾기
/paper-search related arxiv:2301.00001
```

---

## 5. 지원 데이터베이스

| 소스 | 설명 |
|------|------|
| arXiv | 프리프린트 서버 |
| Semantic Scholar | AI 기반 학술 검색 |
| Google Scholar | 학술 검색 엔진 |
| PubMed | 의학/생명과학 논문 |

---

## 6. MCP 도구 목록

| 도구 | 설명 |
|------|------|
| search_papers | 논문 검색 |
| get_paper_details | 논문 상세 정보 |
| get_citations | 인용 정보 조회 |
| get_related_papers | 관련 논문 조회 |

---

## 7. 관련 문서

- `v/oaispaper.md` - 논문 작성 스킬
- `v/oaissurvey.md` - 서베이 논문 작성 스킬
- `v/agent/academic-researcher.md` - 학술 연구 에이전트
