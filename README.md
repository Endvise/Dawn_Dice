# DaWn Dice Party

주사위 파티 이벤트 참여자 예약 시스템

## 프로젝트 개요

**DaWn Dice Party**는 엔티티가 관리하는 주사위 파티 이벤트의 참여자 예약 및 관리 시스템입니다.

- **관리자**: 엔티티
- **기술 스택**: Streamlit + SQLite + Python 3.11+

## 기능

### 사용자 기능
- ✅ 회원가입 (사령관번호 10자리 인증)
- ✅ 로그인 (bcrypt 비밀번호 해싱)
- ✅ 예약 신청 (닉네임, 사령관번호, 서버, 연맹)
- ✅ 내 예약 현황 확인
- ✅ 대기자 순번 확인

### 관리자 기능
- ✅ 예약 승인/거절
- ✅ 참여자 관리 (Excel 불러오기)
- ✅ 블랙리스트 관리 (로컬 + Google Sheets)
- ✅ 공지사항 작성 (Markdown 지원, 상단고정)
- ✅ 회차별 이벤트 세션 관리
- ✅ 실시간 대시보드

### 보안 기능
- ✅ 비밀번호 해싱 (bcrypt)
- ✅ 로그인 실패 제한 (5회)
- ✅ 세션 타임아웃 (60분)
- ✅ 개발자 도구 방지 (F12 차단)
- ✅ 블랙리스트 통합 (로컬 + Google Sheets)

## 프로젝트 구조

```
dice_app/
├── app.py                      # Streamlit 앱 진입점
├── auth.py                      # 인증 시스템
├── database.py                  # 데이터베이스 연산
├── security_utils.py            # 보안 유틸리티 (F12 방지)
├── pages/                      # Streamlit 페이지
│   ├── __init__.py
│   ├── home.py                 # 메인 홈페이지
│   ├── register.py              # 사용자 회원가입
│   ├── reservation.py           # 예약 신청
│   ├── my_reservations.py       # 내 예약 현황
│   ├── admin_reservations.py    # 관리자 예약 관리
│   ├── admin_participants.py    # 관리자 참여자 관리
│   ├── admin_blacklist.py       # 관리자 블랙리스트 관리
│   ├── admin_announcements.py  # 관리자 공지사항 관리
│   ├── admin_dashboard.py       # 관리자 대시보드
│   ├── event_sessions.py        # 회차별 세션 관리
│   └── master_admin.py          # 마스터 관리자 계정 관리
├── DATABASE_SCHEMA.md           # 데이터베이스 스키마 문서
├── SECURITY_GUIDE.md           # 보안 기능 가이드
├── IMPLEMENTATION_PLAN.md       # 구현 계획
├── TEST_PLAN.md               # 테스트 계획
├── SESSION_BASED_RESERVATION_SUMMARY.md  # 세션 기반 예약 요약
└── .streamlit/
    └── secrets.toml.template  # 설정 파일 템플릿
```

## 데이터베이스 구조

| 테이블 | 설명 |
|---------|------|
| users | 사용자 계정 (master, admin, user) |
| reservations | 예약 신청 |
| blacklist | 블랙리스트 (로컬) |
| participants | 기존 참여자 명단 |
| announcements | 공지사항 |
| event_sessions | 회차별 이벤트 세션 |

## 설치 및 실행

### 로컬 개발

```bash
# 의존성 설치
pip install -r requirements.txt

# 또는 uv 사용
uv run pip install -r requirements.txt

# Streamlit 앱 실행
streamlit run dice_app/app.py

# 또는 uv 사용
uv run streamlit run dice_app/app.py
```

### Streamlit Cloud 배포

배포 가이드: [DEPLOYMENT.md](DEPLOYMENT.md)

1. [Streamlit Cloud](https://streamlit.io/cloud) 접속
2. 새 앱 생성
3. Repository: `Endvise/Dawn_Dice`
4. Branch: `master`
5. Main file: `dice_app/app.py`
6. Secrets 설정 (DEPLOYMENT.md 참조)

## 마스터 계정

| 사용자명 | 비밀번호 |
|----------|----------|
| `DaWnntt0623` | `4425endvise9897!` |

⚠️ **보안 경고**: 배포 후 마스터 비밀번호 변경 필수!

## 기술 스택

- **Frontend**: Streamlit 1.28+
- **Backend**: Python 3.11+
- **Database**: SQLite
- **Security**: bcrypt 4.0+
- **Excel**: openpyxl 3.1+
- **HTTP**: requests 2.31+

## 주요 기능

### 회차별 예약 시스템
- 회차별로 이벤트 관리 (세션)
- 최대 참여자: 회차별 180명
- 우선순위 큐:
  - 1순위: 기존 참여자 (이전 회차 참여자)
  - 2순위: 외부 참여자 (새로 가입)
- 대기자 시스템 (FIFO 순서)

### 대기자 시스템
- 정원 초과 시 자동 대기자 명단 등록
- 대기자 순번: 선착순으로 부여
- 승인 시: 대기자 순서대로 승인 가능

### 보안 기능
- F12 개발자 도구 방지 (관리자 제외)
- 로그인 5회 실패 시 계정 잠금
- 세션 60분 자동 로그아웃
- 블랙리스트 통합 (로컬 + Google Sheets)
- bcrypt 비밀번호 해싱 (12 rounds)

## 문서

| 문서 | 설명 |
|------|------|
| [DATABASE_SCHEMA.md](dice_app/DATABASE_SCHEMA.md) | 데이터베이스 스키마 |
| [SECURITY_GUIDE.md](dice_app/SECURITY_GUIDE.md) | 보안 기능 가이드 |
| [IMPLEMENTATION_PLAN.md](dice_app/IMPLEMENTATION_PLAN.md) | 구현 계획 |
| [TEST_PLAN.md](dice_app/TEST_PLAN.md) | 테스트 계획 |
| [DEPLOYMENT.md](DEPLOYMENT.md) | 배포 가이드 |

## GitHub

- **Repository**: https://github.com/Endvise/Dawn_Dice

## 라이선스

프로젝트 내부용 - 엔티티 소유

---

Built with ❤️ for DaWn Dice Party
