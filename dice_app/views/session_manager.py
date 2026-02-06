#!/usr/bin/env python3
"""
Session Manager AI Agent Page

Features:
- Groq Cloud API integration (Llama 3.3 70B)
- Chat interface with conversation history
- Quick action buttons
- Admin/master access control
- Security prompt injection
- Automatic model fallback on rate limit

Access: admin, master only
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from auth import is_authenticated, is_admin, is_master
from database import (
    get_active_session,
    get_all_sessions,
    get_session_check_stats,
    get_session_participants_check,
    list_reservations,
    list_users,
    create_session,
    get_next_session_number,
)
from groq_utils.groq_client import (
    call_groq_api,
    get_groq_config,
    GroqResponse,
    test_groq_connection,
)
from typing import Optional, List, Dict

# Add groq_utils to path
groq_utils_path = str(Path(__file__).parent.parent / "groq_utils")
if groq_utils_path not in sys.path:
    sys.path.insert(0, groq_utils_path)


# =============================================================================
# SECURITY PROMPT - Core system instructions
# =============================================================================

SECURITY_PROMPT = """You are the Session Manager AI Assistant for DaWn Dice Party.

## Your Role
You help administrators manage sessions, users, reservations, and check-ins. You are a READ-ONLY assistant by default, but CAN perform administrative tasks when users ask you to.

## Your Capabilities

### Query (Read-only)
- List users, reservations, participants
- Show statistics and counts
- Search and filter data
- Generate summary reports

### Administrative Actions (When Asked)
- Create new sessions
- Update user information
- Manage reservations
- Any other administrative tasks

## Response Rules
1. Be concise and clear
2. Use tables for lists
3. Include numbers and statistics
4. For data modifications, confirm with user first, then perform the action
5. If you need to create/modify data, call the appropriate function

## Formatting
- Use Korean (한국어) for Korean queries
- Use English for English queries
- Use tables for structured data
- Keep responses concise
- NO repetition of "현재 통계:" or similar headers
- End responses naturally without redundant summaries

## Important
- You CAN perform administrative tasks when asked
- Confirm before making changes, then execute
- Always report the result of your actions
- If an error occurs, explain clearly and suggest solutions"""


# =============================================================================
# Security Functions
# =============================================================================


def check_access_level() -> bool:
    """Check if user is admin or master"""
    if not is_authenticated():
        st.error("먼저 로그인해주세요.")
        return False
    if not is_admin():
        st.error("관리자 권한이 필요합니다.")
        return False
    return True


def validate_user_input(text: str) -> tuple[bool, str]:
    """
    Validate user input for security threats

    Returns: (is_safe, rejection_reason)
    """
    if not text:
        return True, ""

    text_lower = text.lower()

    # Prompt injection patterns
    injection_patterns = [
        "ignore",
        "developer",
        "system prompt",
        "act as",
        "pretend",
        "new instruction",
        "override",
        "you are now",
        "role-play",
        "dan ",
        "sophia",
        "jailbreak",
        "bypass",
        "[system",
        "[new instruction",
        "[override]",
    ]

    for pattern in injection_patterns:
        if pattern.lower() in text_lower:
            return False, f"보안 정책 위반: '{pattern}' 감지됨"

    # Data manipulation patterns
    manipulation_patterns = [
        "delete all",
        "drop table",
        "truncate",
        "update all",
        "delete from",
        "insert into",
        "alter table",
    ]

    for pattern in manipulation_patterns:
        if pattern.lower() in text_lower:
            return False, f"데이터 조작 시도 감지: '{pattern}' 차단됨"

    # External attack patterns
    external_patterns = [
        "http://",
        "https://",
        "www.",
        ".com",
        ".org",
        ".net",
        "javascript:",
        "<script",
        "<iframe",
        "<object>",
    ]

    for pattern in external_patterns:
        if pattern.lower() in text_lower:
            return False, f"외부 공격 패턴 감지: '{pattern}' 차단됨"

    return True, ""


# =============================================================================
# Database Context Functions
# =============================================================================


def get_database_context() -> str:
    """Get current database state for AI context"""
    active_session = get_active_session()
    all_sessions = get_all_sessions()
    active_count = sum(1 for s in all_sessions if s.get("is_active"))

    if not active_session:
        return f"활성 세션: 없음 | 전체 세션: {len(all_sessions)}개"

    session_id = str(active_session["id"])

    try:
        stats = get_session_check_stats(session_id)
    except Exception:
        stats = {
            "total": 0,
            "re_confirmed": 0,
            "alliance_entry": 0,
            "dice_purchased": 0,
        }

    try:
        participants = get_session_participants_check(session_id)
    except Exception:
        participants = []

    try:
        reservations = list_reservations()
    except Exception:
        reservations = []

    context = f"""=== 현재 상태 ===
세션: {active_session.get("session_name", "N/A")} ({active_session.get("session_date", "N/A")})
정원: {active_session.get("max_participants", 180)}명

=== 체크인 ({stats.get("total", 0)}명) ===
재확인: {stats.get("re_confirmed", 0)}명 | 연맹입장: {stats.get("alliance_entry", 0)}명 | 주사위구매: {stats.get("dice_purchased", 0)}명

=== 예약 ===
전체: {len(reservations)}건"""

    return context


# =============================================================================
# Admin Action Handlers
# =============================================================================


def handle_admin_action(action_type: str) -> str:
    """Handle admin actions requested by AI"""
    if action_type == "create_session":
        # Get next session number
        next_num = get_next_session_number()
        return f"새 세션 번호: {next_num}\n\n세션을 생성하려면 다음 정보를 입력하세요:\n- 세션명\n- 세션 날짜 (YYYY-MM-DD)"

    elif action_type == "list_users":
        users = list_users()
        if not users:
            return "등록된 사용자가 없습니다."

        result = f"**전체 사용자 ({len(users)}명)**\n\n"
        result += "| 번호 | 아이디 | 닉네임 | 서버 | 역할 |\n"
        result += "|------|--------|--------|------|------|\n"

        for i, user in enumerate(users[:50], 1):
            result += f"| {i} | {user.get('username', 'N/A')} | {user.get('nickname', 'N/A')} | {user.get('server', 'N/A')} | {user.get('role', 'N/A')} |\n"

        if len(users) > 50:
            result += f"\n... 외 {len(users) - 50}명"

        return result

    elif action_type == "list_sessions":
        sessions = get_all_sessions()
        if not sessions:
            return "등록된 세션이 없습니다."

        result = f"**전체 세션 ({len(sessions)}개)**\n\n"
        result += "| 번호 | 세션명 | 날짜 | 상태 |\n"
        result += "|------|--------|------|------|\n"

        for s in sessions:
            status = "✅ 활성" if s.get("is_active") else "❌ 종료"
            result += f"| {s.get('session_number', 'N/A')} | {s.get('session_name', 'N/A')} | {s.get('session_date', 'N/A')} | {status} |\n"

        return result

    return "알 수 없는 작업입니다."


# =============================================================================
# Quick Actions
# =============================================================================

QUICK_ACTIONS = [
    ("👥 참여자 현황", "현재 세션의 참여자 목록과 체크인 현황을 보여줘"),
    ("📊 체크인 통계", "체크인 통계 (재확인/연맹입장/주사위구매)를 보여줘"),
    ("📋 예약 현황", "예약 승인 대기/승인됨/대기자 현황을 보여줘"),
    ("🔍 사용자 검색", "특정 사용자를 검색하는 방법을 알려줘"),
    ("📈 세션 요약", "현재 세션 전체 요약을 보여줘"),
    ("📋 전체 세션 목록", "모든 세션 목록을 보여줘"),
    ("👤 전체 사용자", "가입된 전체 사용자 목록을 보여줘"),
]

ADMIN_ACTIONS = [
    ("➕ 새 세션 생성", "새 세션을 생성해줘"),
]


# =============================================================================
# Main Page
# =============================================================================


def show():
    """Render the Session Manager AI page"""
    # Access control
    if not check_access_level():
        st.stop()

    # Page title
    st.title("🤖 Session Manager AI")
    st.markdown("---")

    # Get configuration
    config = get_groq_config()

    # Sidebar: Settings
    with st.sidebar:
        st.markdown("### 🤖 AI Settings")

        # API connection status
        if not config.api_key or config.api_key == "YOUR_GROQ_API_KEY":
            st.warning("⚠️ Groq API 키가 설정되지 않았습니다.")
            st.info("""
            **설정 방법:**
            
            `.streamlit/secrets.toml`에 추가:
            ```toml
            GROQ_API_KEY = "your_api_key"
            ```
            
            API 키 발급: https://console.groq.com/keys
            """)
        else:
            st.success("✅ Groq API 연결됨")
            st.markdown(f"**모델:** `{config.primary_model}`")

        st.markdown("---")

        # Parameters
        st.markdown("### ⚙️ Parameters")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        max_tokens = st.number_input("Max Tokens", 100, 4000, 2000)

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ 빠른 질문")

        for label, query in QUICK_ACTIONS:
            if st.button(label, use_container_width=True):
                st.session_state["pending_query"] = query
                st.rerun()

        st.markdown("---")

        # Admin quick actions
        st.markdown("### 🛠️ 관리자 작업")

        for label, query in ADMIN_ACTIONS:
            if st.button(label, use_container_width=True):
                st.session_state["pending_query"] = query
                st.rerun()

        st.markdown("---")

        # Clear conversation
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            if "ai_messages" in st.session_state:
                del st.session_state["ai_messages"]
            if "pending_query" in st.session_state:
                del st.session_state["pending_query"]
            st.rerun()

    # Main area: Chat interface
    st.markdown("### 💬 세션 관리에 대해 질문하세요")

    # Get pending query
    pending_query = st.session_state.pop("pending_query", None)

    # Chat input
    user_input = st.text_area(
        "Your Question",
        value=pending_query or "",
        placeholder="""예시 질문:
- 현재 세션의 재확인 완료한 사람 수를 보여줘
- #095 서버 사용자들의 현황
- 체크인율이 얼마야?
- 예약 승인 대기 중인 사람들
- 홍길동이라는 닉네임을 가진 사람 찾아줘
""",
        height=150,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        send_button = st.button("📤 전송", type="primary", use_container_width=True)

    # Display conversation history
    st.markdown("---")
    st.markdown("#### 💭 대화 기록")

    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    display_messages = [
        m for m in st.session_state["ai_messages"] if m["role"] in ["user", "assistant"]
    ]

    if not display_messages:
        st.info("대화가 없습니다. 질문을 입력하거나 빠른 질문을 선택해주세요.")

    for msg in display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle user input
    if send_button and user_input:
        # Validate input
        is_safe, rejection = validate_user_input(user_input)
        if not is_safe:
            st.error(f"⚠️ {rejection}")
            st.info("다른 질문이나 도움을 드릴 수 있습니다.")
        else:
            # Add user message
            st.session_state["ai_messages"].append(
                {"role": "user", "content": user_input}
            )

            # Get database context
            context = get_database_context()

            # Build messages for API
            messages = [
                {"role": "system", "content": SECURITY_PROMPT},
                {"role": "system", "content": f"\n=== Database Context ===\n{context}"},
            ] + st.session_state["ai_messages"]

            # Show thinking indicator
            with st.chat_message("assistant"):
                with st.spinner("생각 중..."):
                    response = call_groq_api(
                        messages=messages,
                        config=config,
                    )

            if response.success:
                content = response.content
            else:
                error_msg = response.error or "알 수 없는 오류"
                content = f"""⚠️ **API 오류 발생**

{error_msg}

**가능한 원인:**
1. API 키 미설정 또는 오류
2. Rate limit (요청 과다)
3. 네트워크 오류

**해결 방법:**
1. secrets.toml에 GROQ_API_KEY 확인
2. 잠시 후 다시 시도
3. 관리자에게 문의"""

            # Display and save response
            with st.chat_message("assistant"):
                st.markdown(content)

            st.session_state["ai_messages"].append(
                {"role": "assistant", "content": content}
            )

    # Help section
    st.markdown("---")
    st.markdown("""
    ### 💡 사용 가이드
    
    **조회 가능한 정보:**
    - 참여자 현황 및 통계
    - 체크인율 조회
    - 예약 상태 확인
    - 사용자 검색 및 필터링
    - 세션 목록 및 요약
    
    **관리자 작업:**
    - 세션 생성 요청
    - 데이터 조회 및 분석
    - 통계 보고서 생성
    
    **예시 질문:**
    - "현재 세션 참여자 수를 보여줘"
    - "재확인 완료한 사람 목록"
    - "#095 서버 사용자들 현황"
    - "체크인율은 얼마야?"
    - "예약 승인 대기 중인 사람들"
    - "새 세션 생성해줘"
    """)


# =============================================================================
# Run directly
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("Session Manager AI - Direct Test")
    print("=" * 50)

    # Test API connection
    print("\n1. Testing Groq API connection...")
    success, message = test_groq_connection()

    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        print("\nTo configure, add to .streamlit/secrets.toml:")
        print('GROQ_API_KEY = "your_api_key_here"')

    print("\n" + "=" * 50)
    print("Done!")
