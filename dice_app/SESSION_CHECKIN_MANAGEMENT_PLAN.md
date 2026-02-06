# 세션별 체크인 관리 시스템 구현 계획

**작성일**: 2026-02-06
**작성자**: Sisyphus AI Agent

---

## 1. 개요

### 1.1 목표

관리자가 각 세션별로 참여자 체크 상태를 관리할 수 있는 시스템을 구현한다.

### 1.2 주요 기능

- 3가지 체크 유형 관리: 재확인 완료, 연맹 입장 완료, 주사위 구매 완료
- 사령관번호로 빠른 체크인 입력
- 실시간 현황 대시보드 제공
- 기존 participants 테이블과의 연동

---

## 2. 데이터베이스 설계

### 2.1 새 테이블: session_participants

event_sessions와 participants/users를 연결하는 조인 테이블이다.

| 컬럼명 | 타입 | 설명 | 제약조건 |
|--------|------|------|----------|
| id | INTEGER | Primary Key | AUTO_INCREMENT |
| session_id | INTEGER | event_sessions.id | FK, ON DELETE CASCADE |
| user_id | INTEGER | users.id | FK, ON DELETE SET NULL |
| commander_id | TEXT | 사령관번호 | NOT NULL |
| nickname | TEXT | 닉네임 | |
| server | TEXT | 서버 | |
| alliance | TEXT | 연맹 | |
| re_confirmed | BOOLEAN | 재확인 완료 | DEFAULT FALSE |
| alliance_entry | BOOLEAN | 연맹 입장 완료 | DEFAULT FALSE |
| dice_purchased | BOOLEAN | 주사위 구매 완료 | DEFAULT FALSE |
| checked_by | TEXT | 체크한 관리자 | |
| checked_at | TIMESTAMP | 체크 일시 | |
| notes | TEXT | 비고 | |
| created_at | TIMESTAMP | 생성 일시 | DEFAULT CURRENT_TIMESTAMP |

### 2.2 Supabase SQL

```sql
-- 세션별 참여자 체크 테이블 생성
CREATE TABLE session_participants (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES event_sessions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    commander_id TEXT NOT NULL,
    nickname TEXT,
    server TEXT,
    alliance TEXT,
    re_confirmed BOOLEAN DEFAULT FALSE,
    alliance_entry BOOLEAN DEFAULT FALSE,
    dice_purchased BOOLEAN DEFAULT FALSE,
    checked_by TEXT,
    checked_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_session_participants_session ON session_participants(session_id);
CREATE INDEX idx_session_participants_commander ON session_participants(commander_id);
```

---

## 3. 코드 구조

### 3.1 database.py 확장 함수

```python
# 세션 참여자 관리 함수들

def get_session_participants_check(session_id: str) -> List[Dict]:
    """세션별 참여자 체크 상태 조회"""

def add_participant_to_session(
    session_id: str,
    user_id: str,
    commander_id: str,
    nickname: str,
    server: str = None,
    alliance: str = None
) -> int:
    """세션에 참여자 추가"""

def update_participant_check(
    session_id: str,
    commander_id: str,
    check_type: str,  # 're_confirmed', 'alliance_entry', 'dice_purchased'
    checked_by: str
) -> bool:
    """참여자 체크 업데이트"""

def remove_participant_from_session(session_id: str, commander_id: str) -> bool:
    """세션에서 참여자 제거"""

def get_session_check_stats(session_id: str) -> Dict:
    """세션별 체크 현황 통계"""

def bulk_import_session_participants(
    session_id: str,
    participants: List[Dict],
    imported_by: str
) -> tuple[int, int]:
    """엑셀 등으로 대량 참여자 추가 (성공, 실패 수 반환)"""
```

### 3.2 새 뷰 파일: session_checkin.py

```
dice_app/views/session_checkin.py

구조:
- 세션 선택 (dropdown)
- 탭 1: 📋 참여자 목록 (체크박스 관리)
- 탭 2: 🔍 빠른 체크 (사령관번호 입력)
- 탭 3: 📊 현황 통계
```

---

## 4. UI 설계

### 4.1 세션 체크인 관리 페이지

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎯 Session Check-in Management                              │
├─────────────────────────────────────────────────────────────────┤
│ 📁 Select Session: [ Session 5 - Winter Event ▼ ]             │
│                                                                 │
│ ┌──────────────────┬──────────────────┬──────────────────────┐ │
│ │ 📋 Participant    │ 🔍 Quick Check   │ 📊 Statistics        │ │
│ │ List             │                  │                      │ │
│ ├──────────────────┴──────────────────┴──────────────────────┤ │
│ │                                                          │ │
│ │ [사령관번호 입력] [재확인] [연맹입장] [주사위구매] [추가] │ │
│ │                                                          │ │
│ │ ┌────────────────────────────────────────────────────┐   │ │
│ │ │ 👤 Nickname1 (1234567890) - #095 woLF             │   │ │
│ │ │     [✅ 재확인] [✅ 연맹입장] [❌ 주사위]            │   │ │
│ │ │     체크: admin1 | 2024-01-15 14:30               │   │ │
│ │ ├────────────────────────────────────────────────────┤   │ │
│ │ │ 👤 Nickname2 (0987654321) - #708 아시아          │   │ │
│ │ │     [✅ 재확인] [❌ 연맹입장] [❌ 주사위]           │   │ │
│ │ │     체크: - | 대기중                              │   │ │
│ │ └────────────────────────────────────────────────────┘   │ │
│ │                                                          │ │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 빠른 체크 기능 (체크/해제)

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 Quick Check (체크/해제)                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 👤 재확인         │ 👤 연맹 입장      │ 👤 주사위 구매   │ │
│ │ [탭 선택]         │ [탭 선택]         │ [탭 선택]        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Commander ID: [ ________________ ]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ▶ 현재 탭의 상태를 Toggle (체크 ↔ 해제)                       │
│                                                                 │
│ │                    [ ✅ Toggle Status ]                    │ │
│                                                                 │
│ ─────────────────────────────────────────────────────────────  │
│                                                                 │
│ ℹ️ 상태 변경 이력                                            │
│    admin1 → 재확인 체크 (2024-01-15 14:30)                    │
│    admin1 → 재확인 해제 (2024-01-15 15:00)                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 탭별 빠른 작업

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 재확인 탭 - 빠른 작업                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Commander ID: [ ________________ ]                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [ ✅ 체크 ]  [ ❌ 해제 ]                                        │
│                                                                 │
│ → 사령관번호 입력 후 원하는 버튼 클릭                           │
│ → 선택한 탭(재확인)의 상태만 토글                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Admin Dashboard 현황 섹션 추가

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎯 Session Check-in Status                              [+ Expand] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─────────────┬─────────────┬─────────────┬─────────────┐      │
│ │ 재확인 완료  │ 연맹 입장    │ 주사위 구매  │ 미완료       │      │
│ │ 45 / 180    │ 38 / 180     │ 30 / 180    │ 135 / 180   │      │
│ │ 🟢 25%     │ 🟡 21%      │ 🔴 17%     │ ⚠️ 75%     │      │
│ └─────────────┴─────────────┴─────────────┴─────────────┘      │
│                                                                 │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 25% (재확인)    │
│                                                                 │
│ 📊 상세 현황: [View All Sessions ▼]                             │
│                                                                 │
│ Session 5 - Winter Event                                     │
│   - 재확인: 45/180 (25%) | 연맹입장: 38/180 | 주사위: 30/180   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 워크플로우

### 5.1 세션 체크인 프로세스

```
1. 세션 생성 (event_sessions)
           ↓
2. 관리자가 참여자 명단 등록 (세션에 참여자 추가)
           ↓
3. 참여자에게 연락 (재확인 요청)
           ↓
4. 관리자가 체크 입력 (사령관번호로 검색 후 체크)
           ↓
5. 실시간 현황 대시보드로 모니터링
```

### 5.2 체크 상태 전이

```
                              [대기중]
                                  │
                                  ▼
                         ┌───────────────┐
                         │  재확인 완료  │
                         │ (연락 응답)   │
                         └───────┬───────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │  연맹 입장 완료 │
                        └───────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ 주사위 구매 완료 │
                       └─────────────────┘

참고: 각 단계는 독립적으로 트래킹됨
      (순서 상관없이 개별 체크 가능)
```

---

## 6. API 함수 명세

### 6.1 Database Layer Functions

```python
def get_session_participants(session_id: str) -> List[Dict]:
    """
    세션별 참여자 목록 조회 (체크 상태 포함)
    Returns: [
        {
            'id': 1,
            'commander_id': '1234567890',
            'nickname': 'Nickname',
            'server': '#095',
            'alliance': 'DaWn',
            're_confirmed': True,
            'alliance_entry': True,
            'dice_purchased': False,
            'checked_by': 'admin1',
            'checked_at': '2024-01-15T14:30:00',
        },
        ...
    ]
    """

def add_session_participant(
    session_id: str,
    commander_id: str,
    nickname: str,
    server: str = None,
    alliance: str = None,
    added_by: str = None
) -> int:
    """세션에 참여자 추가"""

def toggle_session_check(
    session_id: str,
    commander_id: str,
    check_type: str,  # 're_confirmed', 'alliance_entry', 'dice_purchased'
    checked_by: str
) -> tuple[bool, str]:
    """
    참여자 체크 상태 토글 (체크 ↔ 해제)
    Returns: (success, new_state) - 성공여부와 새로운 상태 반환
    """

def set_session_check(
    session_id: str,
    commander_id: str,
    check_type: str,
    value: bool,
    checked_by: str
) -> bool:
    """참여자 체크 상태 설정 (체크 또는 해제로 명시적 설정)"""

def get_session_check_statistics(session_id: str) -> Dict:
    """
    세션별 체크 현황 통계
    Returns: {
        'total': 180,
        're_confirmed': 45,
        'alliance_entry': 38,
        'dice_purchased': 30,
        'pending': 105,
        're_confirmed_percent': 25.0,
        'completion_rate': 16.7,
    }
    """

def bulk_import_session_participants(
    session_id: str,
    participants: List[Dict],
    imported_by: str
) -> tuple[int, int]:
    """엑셀 등으로 대량 참여자 추가"""
```

### 6.2 View Layer Functions

```python
def show():
    """메인 함수 - 페이지 렌더링"""
    # 1. 세션 선택 dropdown
    # 2. 탭별 콘텐츠 렌더링

def render_participant_list_tab():
    """탭 1: 참여자 목록 (체크박스 관리)"""
    # 데이터테이블로 표시
    # 각 행에 체크박스 3개
    # 필터/정렬 기능

def render_quick_check_tab():
    """탭 2: 빠른 체크 (사령관번호 입력)"""
    # 사령관번호 입력
    # 체크박스 3개
    # 적용 버튼

def render_statistics_tab():
    """탭 3: 현황 통계"""
    # 세션별 현황
    # 차트/그래프
    # 엑셀 다운로드
```

---

## 7. 파일 변경 목록

### 7.1 신규 생성

| 파일 | 설명 |
|------|------|
| `dice_app/database.py` | session_participants 관련 함수 추가 |
| `dice_app/views/session_checkin.py` | 세션 체크인 관리 페이지 |

### 7.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `dice_app/app.py` | 사이드바 메뉴에 "Session Check-in" 추가 |
| `dice_app/views/admin_dashboard.py` | 세션 체크 현황 섹션 추가 |

---

## 8. 구현 우선순위

### Phase 1 (핵심 기능)

1. 데이터베이스 테이블 생성 (Supabase Dashboard에서 수동 실행)
2. `session_checkin.py` 기본 구조
3. 빠른 체크 기능 (사령관번호 입력)
4. 현황 대시보드 (admin_dashboard.py에 추가)

### Phase 2 (확장 기능)

1. 참여자 목록 관리 (데이터테이블)
2. 엑셀 대량 등록
3. 상세 통계 및 차트
4. 엑셀 내보내기

---

## 9. 참고 사항

### 9.1 기존 데이터 활용

- `participants` 테이블의 `event_name` 필드를 세션명과 연결 가능
- 기존 참여자 데이터를 새 테이블로 마이그레이션 가능

### 9.2 Supabase 연동

- 모든 데이터 Supabase REST API를 통해 관리
- 실시간 업데이트는 Supabase Realtime 활용 가능

---

## 10. 예상 작업량

| 항목 | 예상 라인 수 |
|------|-------------|
| Database 함수 | +100 lines |
| Session Check-in 페이지 | +300 lines |
| Admin Dashboard 수정 | +50 lines |
| **총 예상** | **~450 lines** |

---

## 11. 검토 체크리스트

- [ ] 데이터베이스 스키마 승인
- [ ] UI 설계 승인
- [ ] 체크 유형 확인 (재확인, 연맹입장, 주사위구매)
- [ ] 빠른 체크 입력 방식 승인
- [ ] 현황 대시보드 구성 승인
- [ ] Phase 1/2 분할 승인

---

**검토 후 승인하시면 바로 구현 진행하겠습니다.**
