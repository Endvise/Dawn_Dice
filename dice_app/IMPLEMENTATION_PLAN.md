# DaWn Dice Party - 구현 계획

## 문서 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v01 | 2026-01-30 | 초기 구현 계획 작성 |

---

## 1. 프로젝트 개요

### 1.1 프로젝트명
- **DaWn Dice Party** (주사위 파티)
- **관리자**: 엔티티

### 1.2 목적
- 주사위 파티 이벤트 참여자 예약 시스템
- 회차별 참여자 명단 관리
- 선착순 예약 및 대기자 시스템

### 1.3 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Database**: SQLite
- **Security**: bcrypt, Streamlit Secrets
- **Deployment**: Streamlit Cloud (Private Repository)

---

## 2. 요구사항 정리

### 2.1 사용자 기능
| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 회원가입 | 사령관번호(10자리)로 가입 | ⭐⭐⭐ |
| 로그인 | 사령관번호/사용자ID + 비밀번호 | ⭐⭐⭐ |
| 예약 신청 | 닉네임, 사령관번호, 서버, 연맹 입력 | ⭐⭐⭐ |
| 내 예약 현황 | 내 예약/대기 순번 확인 | ⭐⭐⭐ |
| 공지사항 확인 | 홈페이지에서 공지사항 확인 | ⭐⭐ |

### 2.2 관리자 기능 (엔티티)
| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 예약 승인/거절 | 대기 예약 승인 또는 거절 | ⭐⭐⭐ |
| 예약 수정/삭제 | 예약자 정보 수정 및 삭제 | ⭐⭐ |
| 참여자 관리 | 기존 참여자 명단 관리 | ⭐⭐⭐ |
| 블랙리스트 관리 | 블랙리스트 추가/제거 | ⭐⭐⭐ |
| 공지사항 작성 | 공지사항/안내 작성 및 게시 | ⭐⭐ |
| 회차별 명단 관리 | 회차별 참여자 명단 관리 | ⭐⭐⭐ |
| 이전 회차 불러오기 | 이전 회차 명단 가져오기 | ⭐⭐⭐ |

### 2.3 마스터 기능
| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 관리자 계정 생성 | 하위 관리자 계정 생성 | ⭐⭐⭐ |
| 관리자 계정 관리 | 관리자 정보 수정/삭제 | ⭐⭐ |

### 2.4 보안 기능
| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 비밀번호 해싱 | bcrypt로 비밀번호 해싱 | ⭐⭐⭐ |
| 로그인 실패 제한 | 5회 실패 시 계정 잠금 | ⭐⭐⭐ |
| 세션 타임아웃 | 60분 자동 로그아웃 | ⭐⭐ |
| 개발자 도구 방지 | F12 방지 및 관리자만 해제 | ⭐⭐⭐ |
| Secrets 관리 | Streamlit Cloud Secrets 사용 | ⭐⭐⭐ |
| 블랙리스트 | 로컬 + Google Sheets 통합 | ⭐⭐⭐ |

---

## 3. 데이터베이스 설계

### 3.1 테이블 구조

#### users (사용자)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| username | TEXT | 사용자 ID (마스터/관리자) |
| commander_id | TEXT | 사령관번호 (사용자) |
| password_hash | TEXT | 비밀번호 해시 |
| role | TEXT | 역할 (master, admin, user) |
| nickname | TEXT | 닉네임 |
| server | TEXT | 서버 |
| alliance | TEXT | 연맹 |
| is_active | BOOLEAN | 활성화 여부 |
| created_at | TIMESTAMP | 생성일시 |
| last_login | TIMESTAMP | 마지막 로그인 |
| failed_attempts | INTEGER | 로그인 실패 횟수 |

#### reservations (예약)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| user_id | INTEGER | FK(users.id) |
| nickname | TEXT | 닉네임 |
| commander_id | TEXT | 사령관번호 |
| server | TEXT | 서버 (자유 입력) |
| alliance | TEXT | 연맹 (자유 입력) |
| status | TEXT | 상태 (pending, approved, rejected, cancelled, waitlisted) |
| is_blacklisted | BOOLEAN | 블랙리스트 여부 |
| blacklist_reason | TEXT | 블랙리스트 사유 |
| created_at | TIMESTAMP | 신청일시 (선착순 기록) |
| approved_at | TIMESTAMP | 승인일시 |
| approved_by | INTEGER | 승인자(users.id) |
| notes | TEXT | 비고 |
| waitlist_order | INTEGER | 대기자 순번 |
| waitlist_position | INTEGER | 대기자 현재 위치 |

#### blacklist (블랙리스트)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| commander_id | TEXT | 사령관번호 (UNIQUE) |
| nickname | TEXT | 닉네임 |
| reason | TEXT | 사유 |
| added_at | TIMESTAMP | 추가일시 |
| added_by | INTEGER | 추가자(users.id) |
| is_active | BOOLEAN | 활성화 여부 |

#### participants (기존 참여자)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| number | INTEGER | 번호 |
| nickname | TEXT | 닉네임 |
| affiliation | TEXT | 소속 |
| igg_id | TEXT | IGG 아이디 (사령관번호) |
| alliance | TEXT | 연맹 |
| wait_confirmed | BOOLEAN | 대기확인 |
| confirmed | BOOLEAN | 확인 |
| notes | TEXT | 비고 |
| completed | BOOLEAN | 참여완료 |
| participation_record | TEXT | 참여기록 |
| event_name | TEXT | 이벤트명 |
| created_at | TIMESTAMP | 생성일시 |

#### announcements (공지사항)
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| title | TEXT | 제목 |
| content | TEXT | 내용 (Markdown) |
| category | TEXT | 카테고리 (공지, 안내, 이벤트) |
| is_pinned | BOOLEAN | 상단 고정 여부 |
| created_by | INTEGER | 작성자(users.id) |
| created_at | TIMESTAMP | 생성일시 |
| updated_at | TIMESTAMP | 수정일시 |
| is_active | BOOLEAN | 활성화 여부 |

#### event_sessions (이벤트 회차) - NEW
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | PK, AUTO_INCREMENT |
| session_number | INTEGER | 회차 번호 |
| session_name | TEXT | 회차명 |
| session_date | DATE | 회차 날짜 |
| max_participants | INTEGER | 최대 참여자 (180) |
| is_active | BOOLEAN | 활성화 여부 |
| created_by | INTEGER | 생성자(users.id) |
| created_at | TIMESTAMP | 생성일시 |

---

## 4. 구현 현황

### 4.1 완료 ✅ (Phase 1 개발 완료)
| 모듈 | 파일 | 상태 | 완료 일시 |
|------|------|------|----------|
| 데이터베이스 스키마 | `database.py` | ✅ | 2026-01-30 |
| 인증 시스템 | `auth.py` | ✅ | 2026-01-30 |
| 사용자 등록 | `pages/register.py` | ✅ | 2026-01-30 |
| 예약 신청 | `pages/reservation.py` | ✅ | 2026-01-30 |
| 내 예약 현황 | `pages/my_reservations.py` | ✅ | 2026-01-30 |
| 관리자 예약 관리 | `pages/admin_reservations.py` | ✅ | 2026-01-30 |
| 관리자 참여자 관리 | `pages/admin_participants.py` | ✅ | 2026-01-30 |
| 관리자 블랙리스트 관리 | `pages/admin_blacklist.py` | ✅ | 2026-01-30 |
| 관리자 공지사항 관리 | `pages/admin_announcements.py` | ✅ | 2026-01-30 |
| 마스터 관리자 계정 관리 | `pages/master_admin.py` | ✅ | 2026-01-30 |
| 회차별 명단 관리 | `pages/event_sessions.py` | ✅ | 2026-01-30 |
| 관리자 대시보드 | `pages/admin_dashboard.py` | ✅ | 2026-01-30 |
| 메인 홈페이지 | `pages/home.py` | ✅ | 2026-01-30 |
| 보안 가이드 | `SECURITY_GUIDE.md` | ✅ | 2026-01-30 |
| 개발자 도구 방지 | `security_utils.py` | ✅ | 2026-01-30 |
| Secrets 설정 | `.streamlit/secrets.toml` | ✅ | 2026-01-30 |

### 4.2 테스트 및 배포 (Phase 1 마무리)
| 작업 | 상태 | 우선순위 |
|------|------|----------|
| 기능 테스트 | ⏳ | ⭐⭐⭐ |
| 보안 테스트 | ⏳ | ⭐⭐⭐ |
| 배포 준비 | ⏳ | ⭐⭐⭐ |

### 4.3 Phase 2 예정
| 기능 | 우선순위 |
|------|----------|
| 로그 시스템 | ⭐⭐⭐ |
| 2FA (이중 인증) | ⭐⭐⭐ |
| 이메일 알림 | ⭐⭐ |
| API 연동 | ⭐ |
| 모바일 최적화 | ⭐ |

---

## 5. 구현 계획

### 5.1 단계 1: 필수 페이지 완성 (우선순위: ⭐⭐⭐)

#### Task 1.1: 관리자 참여자 관리 페이지
- **파일**: `pages/admin_participants.py`
- **기능**:
  - 참여자 목록 표시
  - 참여자 추가/수정/삭제
  - 회차별 필터링
  - Excel 불러오기 기능
  - 대기자 순번 관리
- **완료 기준**: CRUD 기능 완료, 테스트 통과

#### Task 1.2: 관리자 블랙리스트 관리 페이지
- **파일**: `pages/admin_blacklist.py`
- **기능**:
  - 블랙리스트 목록 표시
  - 블랙리스트 추가 (사령관번호, 사유)
  - 블랙리스트 제거/복원
  - Google Sheets 동기화 표시
- **완료 기준**: CRUD 기능 완료, Google Sheets 연동

#### Task 1.3: 관리자 공지사항 관리 페이지
- **파일**: `pages/admin_announcements.py`
- **기능**:
  - 공지사항 작성 (제목, 내용, 카테고리)
  - 공지사항 수정/삭제
  - 상단 고정 설정
  - Markdown 지원
- **완료 기준**: CRUD 기능 완료, 미리보기

#### Task 1.4: 마스터 관리자 계정 관리 페이지
- **파일**: `pages/master_admin.py`
- **기능**:
  - 관리자 계정 생성 (아이디, 비밀번호, 권한)
  - 관리자 정보 수정/삭제
  - 관리자 목록 표시
  - 비밀번호 초기화
- **완료 기준**: CRUD 기능 완료, 권한 체크

### 5.2 단계 2: 회차별 명단 관리 (우선순위: ⭐⭐⭐)

#### Task 2.1: Excel 회차 명단 로더
- **파일**: `utils/excel_loader.py`
- **기능**:
  - Excel 파일 읽기
  - 시트별 회차 식별 (날짜 기반)
  - 데이터 파싱 및 정제
  - DB에 저장
- **완료 기준**: Excel → DB 변환 성공

#### Task 2.2: 회차별 명단 관리 페이지
- **파일**: `pages/event_sessions.py`
- **기능**:
  - 회차 생성 (회차명, 날짜)
  - 회차 목록 표시
  - 이전 회차 명단 불러오기
  - 회차별 참여자 표시
- **완료 기준**: 회차 CRUD 완료, Excel 연동

### 5.3 단계 3: 메인 홈페이지 완성 (우선순위: ⭐⭐)

#### Task 3.1: 메인 페이지 개선
- **파일**: `pages/home.py`
- **기능**:
  - 예약 상태 표시 (예약 가능/마감)
  - 공지사항 최신 목록
  - 사용자별 메시지
  - 블랙리스트 경고
- **완료 기준**: UI 개선, 기능 완료

### 5.4 단계 4: 테스트 및 배포 (우선순위: ⭐⭐)

#### Task 4.1: 기능 테스트
- **테스트 항목**:
  - 사용자 회원가입/로그인
  - 예약 신청/취소
  - 대기자 순번 계산
  - 블랙리스트 차단
  - 공지사항 작성/표시
  - 관리자 CRUD 기능
  - 회차별 명단 관리
- **완료 기준**: 모든 테스트 통과

#### Task 4.2: 보안 테스트
- **테스트 항목**:
  - F12 개발자 도구 방지
  - 로그인 실패 제한
  - 세션 타임아웃
  - SQL Injection 방지
  - XSS 방지
- **완료 기준**: 모든 보안 테스트 통과

#### Task 4.3: 배포 준비
- **배포 체크리스트**:
  - [ ] Secrets 설정 완료
  - [ ] .gitignore 확인 (secrets.toml, DB)
  - [ ] GitHub Repository 설정 (Private)
  - [ ] Streamlit Cloud 연동
  - [ ] 마스터 계정 확인
  - [ ] Google Sheets URL 확인
- **완료 기준**: 배포 성공

---

## 6. 우선순위 기준

| 우선순위 | 설명 |
|----------|------|
| ⭐⭐⭐ | 필수 기능 (MVP) |
| ⭐⭐ | 중요 기능 |
| ⭐ | 추가 기능 |

---

## 7. 일정 계획

| 단계 | 작업 | 예상 기간 |
|------|------|----------|
| 단계 1 | 필수 페이지 완성 | 2-3일 |
| 단계 2 | 회차별 명단 관리 | 1-2일 |
| 단계 3 | 메인 홈페이지 완성 | 1일 |
| 단계 4 | 테스트 및 배포 | 1-2일 |
| **총계** | | **5-8일** |

---

## 8. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Excel 데이터 형식 불일치 | 높 | 데이터 정규화 프로세스 추가 |
| Google Sheets 연동 실패 | 중 | 로컬 블랙리스트로 대체 |
| Streamlit Cloud 제한 | 중 | 배포 옵션 (Vercel, AWS) 확인 |
| 보안 이슈 발생 | 높 | 정기 보안 감사, 취약점 점검 |
| 대기자 순번 오류 | 높 | 단위 테스트 강화 |

---

## 9. 완료 기준

### 9.1 기능적 완료
- ✅ 모든 필수 기능 구현
- ✅ 모든 CRUD 기능 완료
- ✅ 예약/대기자 시스템 정상 작동

### 9.2 보안적 완료
- ✅ 보안 가이드 모든 항목 이행
- ✅ 취약점 없음
- ✅ 마스터 계정 보안 완료

### 9.3 배포 완료
- ✅ Streamlit Cloud 배포 성공
- ✅ 모든 테스트 통과
- ✅ 사용자 매뉴얼 작성

---

## 10. 향후 개선 (Phase 2)

| 기능 | 설명 |
|------|------|
| 2FA (이중 인증) | 마스터 계정 2FA 도입 |
| 이메일 알림 | 예약 승인/대기자 알림 |
| 대시보드 | 실시간 통계 대시보드 |
| 로그 시스템 | 보안 로그 및 감사 |
| API | 외부 연동 API |
| 모바일 최적화 | 반응형 UI 개선 |

---

## 11. Phase 2 계획 (차후 도입)

### 11.1 완료된 기능
| 기능 | 파일 | 완료 일시 |
|------|------|----------|
| 관리자 대시보드 | `pages/admin_dashboard.py` | 2026-01-30 |

### 11.2 로그 시스템
- **파일**: `pages/admin_logs.py`
- **기능**:
  - 로그인 기록 (사용자, IP, 시간)
  - 보안 이슈 (F12 시도, SQL Injection 시도)
  - 시스템 이벤트 (예약, 승인, 거절)
  - 관리자 액션 로그
- **우선순위**: ⭐⭐⭐

### 11.3 2FA (이중 인증)
- **파일**: `auth.py`
- **기능**:
  - 마스터 계정 TOTP (Google Authenticator)
  - 2FA 설정/해제
  - 백업 코드 제공
- **우선순위**: ⭐⭐⭐

### 11.4 이메일 알림
- **파일**: `utils/email.py`
- **기능**:
  - 예약 승인 알림
  - 대기자 순번 알림
  - 블랙리스트 추가 알림
  - 공지사항 알림
- **우선순위**: ⭐⭐

### 11.5 API 연동
- **파일**: `api/` 디렉토리
- **기능**:
  - Discord Webhook 연동
  - REST API (GET/POST)
  - Webhook 이벤트 트리거
- **우선순위**: ⭐

### 11.6 모바일 최적화
- **파일**: `pages/` 전체
- **기능**:
  - 반응형 UI
  - 모바일 최적화
  - PWA 지원 (선택)
- **우선순위**: ⭐

---

## 12. Phase 2 우선순위

| 순위 | 기능 | 이유 |
|------|------|------|
| 1 | 로그 시스템 | 보안 감사 중요 |
| 2 | 2FA | 마스터 계정 보안 강화 |
| 3 | 이메일 알림 | 사용자 경험 개선 |
| 4 | API 연동 | 외부 연동 필요 시 |
| 5 | 모바일 최적화 | 사용자 편의성 |

---

## 13. Phase 2 일정 계획

| 순서 | 작업 | 예상 기간 |
|------|------|----------|
| 1 | 로그 시스템 구현 | 2-3일 |
| 2 | 2FA 도입 | 2일 |
| 3 | 이메일 알림 | 2-3일 |
| 4 | API 연동 | 3-4일 |
| 5 | 모바일 최적화 | 2-3일 |
| **총계** | | **11-15일** |

