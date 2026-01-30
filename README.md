# 시니어포탈 (Senior Portal)

시니어 세대를 위한 통합 정보 서비스 플랫폼

## 프로젝트 구조

```
0002_SApp/
├── 01_algorithm/       # 알고리즘 서브프로젝트
├── 02_1st_server/      # 1차 서버 (Streamlit 웹앱)
│   ├── pages/          # Streamlit 페이지 (40+ 페이지)
│   ├── login.py        # 로그인 시스템
│   └── config.py       # 설정 파일
├── db/                 # SQLite 데이터베이스
│   └── silver.sqlite   # 메인 DB (17개 테이블)
├── doc/                # 프로젝트 문서
│   ├── d0001_prd.md    # 제품 요구사항 정의서
│   ├── d0004_todo.md   # TODO 및 디버깅
│   ├── d0005_lib.md    # 라이브러리 문서 (43개 모듈)
│   ├── d0006_db.md     # DB 스키마 문서
│   └── d0010_history.md # 변경 이력
├── oais/               # 공통 유틸리티 모듈
├── tests/              # 테스트 코드
└── v/                  # 스킬 문서 (oais*.md)
```

## 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Database**: SQLite
- **Package Manager**: uv

## 실행 방법

```bash
# 개발 서버 실행
uv run streamlit run 02_1st_server/login.py

# 테스트 실행
uv run pytest tests/ -v
```

## 최근 작업 내역

### 2026-01-05
- **oaistest 스킬 정합성 개선**
  - test_guide.md Part E 섹션 추가 (런타임 검증)
  - oaistest.md 3건 정합성 수정 (Part D/E 에이전트, 모듈 수 43개)
  - Part D refresh 제거 → run 시 자동 재스캔으로 변경
- **todo137~143 아카이브 완료** (d20010 이동)
  - 시니어콘텐츠카드 work 유형, 74페이지 탭, Django 환경 등 7건

### 2026-01-02
- **oaisrun run 프로젝트 건강검진 완료**
  - A003: 시스템관리.py bare except 수정
  - A004: copy_test_accounts.py 하드코딩 경로 수정
  - d0006_db.md 누락 컬럼 추가 (user_grade, mobile)
  - pytest 59 tests passed

- **프로젝트 전체 정리**
  - 40개 이상 Streamlit 페이지 추가
  - 스킬 문서 간소화 및 통합
  - 서브프로젝트별 PRD 문서 추가

## 다음 작업

- [ ] 70번대 앱 페이지 개발 계속 (d20011 앱개발계획 참조)
- [ ] Part B E2E 테스트 구현 (Playwright)
- [ ] 03_app_design Django 개발 시작

## 문서 참조

| 문서 | 설명 |
|------|------|
| doc/d0001_prd.md | 제품 요구사항 정의서 |
| doc/d0004_todo.md | TODO 및 디버깅 관리 |
| doc/d0005_lib.md | oais 모듈 문서 |
| doc/d0006_db.md | DB 스키마 문서 |
| CLAUDE.md | Claude Code 설정 |

---

Generated with Claude Code
