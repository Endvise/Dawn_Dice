# 주사위 예약 시스템 - 데이터베이스 스키마

## 테이블 설계

### 1. users (사용자 계정 테이블)
사용자 계정과 권한을 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| username | TEXT | 사용자 ID (마스터/관리자용) | UNIQUE, NOT NULL |
| commander_id | TEXT | 사령관번호 (외부 사용자용) | UNIQUE |
| password_hash | TEXT | 비밀번호 해시 | NOT NULL |
| role | TEXT | 역할 (master, admin, user) | NOT NULL, DEFAULT 'user' |
| nickname | TEXT | 닉네임 | |
| server | TEXT | 서버 번호 (예: #095) | |
| alliance | TEXT | 연맹 이름 | |
| is_active | BOOLEAN | 계정 활성화 여부 | DEFAULT 1 |
| created_at | TIMESTAMP | 생성 일시 | DEFAULT CURRENT_TIMESTAMP |
| last_login | TIMESTAMP | 마지막 로그인 | |
| failed_attempts | INTEGER | 로그인 실패 횟수 | DEFAULT 0 |

### 2. reservations (예약 신청 테이블)
외부 사용자의 예약 신청을 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| user_id | INTEGER | users 테이블 외래키 | FOREIGN KEY(users.id) |
| nickname | TEXT | 닉네임 | NOT NULL |
| commander_id | TEXT | 사령관번호 | NOT NULL |
| server | TEXT | 서버 번호 | NOT NULL |
| alliance | TEXT | 연맹 이름 | |
| status | TEXT | 상태 (pending, approved, rejected, cancelled, waitlisted) | DEFAULT 'pending' |
| is_blacklisted | BOOLEAN | 블랙리스트 여부 | DEFAULT 0 |
| blacklist_reason | TEXT | 블랙리스트 사유 | |
| created_at | TIMESTAMP | 신청 일시 | DEFAULT CURRENT_TIMESTAMP |
| approved_at | TIMESTAMP | 승인 일시 | |
| approved_by | INTEGER | 승인자(users.id) | FOREIGN KEY(users.id) |
| notes | TEXT | 비고 | |
| waitlist_order | INTEGER | 대기자 순번 | |
| waitlist_position | INTEGER | 대기자 현재 위치 | |

### 3. blacklist (블랙리스트 테이블)
로컬 블랙리스트를 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| commander_id | TEXT | 사령관번호 | UNIQUE, NOT NULL |
| nickname | TEXT | 닉네임 | |
| reason | TEXT | 블랙리스트 사유 | |
| added_at | TIMESTAMP | 추가 일시 | DEFAULT CURRENT_TIMESTAMP |
| added_by | INTEGER | 추가자(users.id) | FOREIGN KEY(users.id) |
| is_active | BOOLEAN | 활성화 여부 | DEFAULT 1 |

### 4. servers (서버 정보 테이블)
서버 정보를 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| server_name | TEXT | 서버 이름 (예: #095 woLF) | UNIQUE, NOT NULL |
| server_code | TEXT | 서버 코드 (예: #095) | UNIQUE |
| is_active | BOOLEAN | 활성화 여부 | DEFAULT 1 |

### 5. alliances (연맹 정보 테이블)
연맹 정보를 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| alliance_name | TEXT | 연맹 이름 | UNIQUE, NOT NULL |
| server_id | INTEGER | 소속 서버 | FOREIGN KEY(servers.id) |
| is_active | BOOLEAN | 활성화 여부 | DEFAULT 1 |

### 6. participants (참여자 목록 테이블)
엑셀에서 가져온 기존 참여자 목록입니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| number | INTEGER | 번호 | |
| nickname | TEXT | 닉네임 | |
| affiliation | TEXT | 소속 | |
| igg_id | TEXT | IGG 아이디 (사령관번호) | |
| alliance | TEXT | 연맹 | |
| wait_confirmed | BOOLEAN | 대기확인 | DEFAULT 0 |
| confirmed | BOOLEAN | 확인 | DEFAULT 0 |
| notes | TEXT | 비고 | |
| completed | BOOLEAN | 참여완료 | DEFAULT 0 |
| participation_record | TEXT | 참여기록 | |
| event_name | TEXT | 이벤트명 | |
| created_at | TIMESTAMP | 생성 일시 | DEFAULT CURRENT_TIMESTAMP |

### 7. announcements (공지사항 테이블)
공지사항 및 안내를 관리합니다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT, PRIMARY KEY |
| title | TEXT | 제목 | NOT NULL |
| content | TEXT | 내용 (Markdown 지원) | NOT NULL |
| category | TEXT | 카테고리 (공지, 안내, 이벤트) | DEFAULT '공지' |
| is_pinned | BOOLEAN | 상단 고정 여부 | DEFAULT 0 |
| created_by | INTEGER | 작성자(users.id) | FOREIGN KEY(users.id) |
| created_at | TIMESTAMP | 생성 일시 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | 수정 일시 | |
| is_active | BOOLEAN | 활성화 여부 | DEFAULT 1 |

## 보안 관련

### Secrets 관리 (Streamlit Cloud)
`.streamlit/secrets.toml` 파일에 다음 키를 관리:

```toml
# 마스터 계정 정보
MASTER_USERNAME = "DaWnntt0623"
MASTER_PASSWORD = "4425endvise9897!"

# Google Sheets 블랙리스트 URL
BLACKLIST_GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1zCiNgbWtl6IWsla3Vz9NMFA2hxO978L9lN1n1gfsEyA/export?format=csv"

# 데이터베이스 설정 (필요한 경우)
# DB_PATH = "data/dice_app.db"
```

## 인덱스

```sql
CREATE INDEX idx_users_commander_id ON users(commander_id);
CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_blacklist_commander_id ON blacklist(commander_id);
CREATE INDEX idx_participants_igg_id ON participants(igg_id);
```

## 초기 데이터

### 마스터 계정
- username: DaWnntt0623
- password: 4425endvise9897!
- role: master

### 기본 서버
- #095 woLF
- #708 아시아
- (엑셀에서 추출)
