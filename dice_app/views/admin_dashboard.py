#!/usr/bin/env python3
"""
관리자 대시보드 페이지 (실시간 통계)
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from datetime import datetime, timedelta


def get_dashboard_stats() -> dict:
    """대시보드 통계를 반환합니다."""
    # 사용자 통계
    total_users = len(db.list_users())
    active_users = len(db.list_users(is_active=True))
    admin_users = len(db.list_users(role="admin"))

    # 예약 통계
    all_reservations = db.list_reservations()

    pending = len([r for r in all_reservations if r["status"] == "pending"])
    approved = len([r for r in all_reservations if r["status"] == "approved"])
    rejected = len([r for r in all_reservations if r["status"] == "rejected"])
    cancelled = len([r for r in all_reservations if r["status"] == "cancelled"])
    waitlisted = len([r for r in all_reservations if r["status"] == "waitlisted"])

    # 블랙리스트 통계
    blacklist = db.list_blacklist(is_active=True)

    # 참여자 통계
    participants = db.list_participants()
    completed = len([p for p in participants if p.get("completed")])
    confirmed = len([p for p in participants if p.get("confirmed")])

    # 공지사항 통계
    announcements = db.list_announcements(is_active=True)
    pinned = len([a for a in announcements if a.get("is_pinned")])

    # 총 참여자 수 (기존 + 승인된 예약)
    total_participants = completed + approved

    return {
        "users": {"total": total_users, "active": active_users, "admin": admin_users},
        "reservations": {
            "total": len(all_reservations),
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "cancelled": cancelled,
            "waitlisted": waitlisted,
        },
        "blacklist": {"total": len(blacklist)},
        "participants": {
            "total": len(participants),
            "completed": completed,
            "confirmed": confirmed,
        },
        "announcements": {"total": len(announcements), "pinned": pinned},
        "overall": {
            "total_participants": total_participants,
            "max_participants": db.MAX_PARTICIPANTS,
            "is_full": total_participants >= db.MAX_PARTICIPANTS,
            "waitlist_count": waitlisted,
        },
    }


def get_reservation_trend(days: int = 7) -> list:
    """예약 추이를 반환합니다."""
    trend = []

    for i in range(days):
        date = datetime.now() - timedelta(days=days - 1 - i)
        date_str = date.strftime("%Y-%m-%d")

        # 해당 날짜의 예약 수
        result = execute_query(
            """
            SELECT COUNT(*) as count
            FROM reservations
            WHERE DATE(created_at) = ?
            """,
            (date_str,),
            fetch="one",
        )

        count = result["count"] if result and "count" in result else 0
        trend.append({"date": date_str, "count": count})

    return trend


def show():
    """대시보드 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("📊 대시보드")
    st.markdown("---")

    # 실시간 업데이트
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

    # 기간 선택
    col1, col2 = st.columns([1, 2])

    with col1:
        trend_days = st.selectbox("추이 기간", [7, 14, 30], index=0)

    with col2:
        st.info(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 통계 가져오기
    stats = get_dashboard_stats()

    # ===== 메인 카드 =====
    st.markdown("## 📋 주요 통계")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if stats["overall"]["is_full"]:
            st.error("⛔ 예약 마감")
        else:
            st.success("✅ 예약 가능")

        st.metric(
            "참여자",
            f"{stats['overall']['total_participants']} / {stats['overall']['max_participants']}명",
            delta=f"{stats['overall']['waitlist_count']}명 대기중",
            delta_color="normal" if stats["overall"]["waitlist_count"] > 0 else "off",
        )

    with col2:
        st.metric("예약 대기중", f"{stats['reservations']['pending']}건")

    with col3:
        st.metric("승인된 예약", f"{stats['reservations']['approved']}건")

    with col4:
        st.metric("대기자", f"{stats['reservations']['waitlisted']}명")

    st.markdown("---")

    # ===== 카테고리별 통계 =====
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["👤 사용자", "📝 예약", "👥 참여자", "🚫 블랙리스트", "📢 공지사항"]
    )

    # 탭 1: 사용자
    with tab1:
        st.markdown("### 👤 사용자 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("전체 사용자", f"{stats['users']['total']}명")

        with col2:
            st.metric("활성 사용자", f"{stats['users']['active']}명")

        with col3:
            st.metric("관리자", f"{stats['users']['admin']}명")

        # 사용자 목록
        st.markdown("#### 📋 사용자 목록")

        users_list = db.list_users()

        if users_list:
            for user_data in users_list:
                role_badge = {"master": "👑", "admin": "🛡️", "user": "👤"}

                badge = role_badge.get(user_data["role"], "👤")

                with st.expander(
                    f"{badge} {user_data.get('username', user_data.get('commander_id', 'Unknown'))} - {user_data.get('nickname', 'Unknown')}"
                ):
                    st.markdown(f"""
                    **역할**: {user_data.get("role", "Unknown")}
                    **서버**: {user_data.get("server", "N/A")}
                    **연맹**: {user_data.get("alliance", "없음") if user_data.get("alliance") else "없음"}
                    **생성일시**: {user_data.get("created_at", "N/A")}
                    **마지막 로그인**: {user_data.get("last_login", "N/A") if user_data.get("last_login") else "없음"}
                    **활성화**: {"활성" if user_data.get("is_active") else "비활성"}
                    """)

                    if user_data.get("failed_attempts", 0) > 0:
                        st.warning(f"⚠️ 로그인 실패: {user_data['failed_attempts']}회")

                    # 로그인 실패 초기화 버튼
                    if user_data.get("failed_attempts", 0) > 0 and is_master:
                        if st.button(
                            "실패 횟수 초기화",
                            key=f"reset_failed_{user_data['id']}",
                            use_container_width=True,
                        ):
                            db.update_user(user_data["id"], failed_attempts=0)
                            st.success("✓ 초기화되었습니다.")
                            st.rerun()

        else:
            st.info("등록된 사용자가 없습니다.")

    # 탭 2: 예약
    with tab2:
        st.markdown("### 📝 예약 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("전체 예약", f"{stats['reservations']['total']}건")

        with col2:
            st.metric("대기중", f"{stats['reservations']['pending']}건")

        with col3:
            st.metric(
                "완료",
                f"{stats['reservations']['approved'] + stats['reservations']['rejected']}건",
            )

        # 예약 상태 분포
        st.markdown("#### 📊 예약 상태 분포")

        status_data = [
            {"상태": "대기중", "건수": stats["reservations"]["pending"]},
            {"상태": "승인됨", "건수": stats["reservations"]["approved"]},
            {"상태": "거절됨", "건수": stats["reservations"]["rejected"]},
            {"상태": "취소됨", "건수": stats["reservations"]["cancelled"]},
            {"상태": "대기자", "건수": stats["reservations"]["waitlisted"]},
        ]

        for data in status_data:
            color = {
                "대기중": "🟡",
                "승인됨": "🟢",
                "거절됨": "🔴",
                "취소됨": "⚪",
                "대기자": "🔵",
            }

            badge = color.get(data["상태"], "❓")
            percentage = (
                (data["건수"] / stats["reservations"]["total"] * 100)
                if stats["reservations"]["total"] > 0
                else 0
            )

            st.markdown(f"""
            **{badge} {data["상태"]}**: {data["건수"]}건 ({percentage:.1f}%)
            """)

        # 예약 추이
        st.markdown("---")
        st.markdown(f"#### 📈 최근 {trend_days}일 예약 추이")

        trend = get_reservation_trend(trend_days)

        if trend:
            import pandas as pd

            df = pd.DataFrame(trend)
            st.line_chart(df.set_index("date"))
        else:
            st.info("데이터가 없습니다.")

    # 탭 3: 참여자
    with tab3:
        st.markdown("### 👥 참여자 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("전체 참여자", f"{stats['participants']['total']}명")

        with col2:
            st.metric("참여완료", f"{stats['participants']['completed']}명")

        with col3:
            st.metric("확인됨", f"{stats['participants']['confirmed']}명")

        # 이벤트별 참여자
        st.markdown("#### 📋 이벤트별 참여자")

        participants_list = db.list_participants()

        if participants_list:
            # 이벤트별 그룹화
            event_stats = {}

            for p in participants_list:
                event_name = p["event_name"] if p and "event_name" in p else "Unknown"

                if event_name not in event_stats:
                    event_stats[event_name] = {
                        "total": 0,
                        "completed": 0,
                        "confirmed": 0,
                    }

                event_stats[event_name]["total"] += 1

                if p["completed"] if p and "completed" in p else False:
                    event_stats[event_name]["completed"] += 1

                if p["confirmed"] if p and "confirmed" in p else False:
                    event_stats[event_name]["confirmed"] += 1

            # 표시
            for event_name, data in sorted(event_stats.items()):
                with st.expander(f"🎉 {event_name}"):
                    st.markdown(f"""
                    **전체**: {data["total"]}명
                    **참여완료**: {data["completed"]}명
                    **확인됨**: {data["confirmed"]}명
                    """)

        else:
            st.info("참여자 데이터가 없습니다.")

    # 탭 4: 블랙리스트
    with tab4:
        st.markdown("### 🚫 블랙리스트 통계")

        st.metric("활성 블랙리스트", f"{stats['blacklist']['total']}명")

        # 블랙리스트 목록
        st.markdown("#### 📋 블랙리스트 목록")

        blacklist_list = db.list_blacklist(is_active=True)

        if blacklist_list:
            for bl in blacklist_list:
                with st.expander(
                    f"🚫 {bl['commander_id']} - {bl['nickname'] if bl and 'nickname' in bl else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **사령관번호**: {bl["commander_id"]}
                    **닉네임**: {bl["nickname"] if bl and "nickname" in bl else "Unknown"}
                    **사유**: {bl["reason"] if bl and "reason" in bl else "N/A"}
                    **추가일시**: {bl["added_at"]}
                    """)

        else:
            st.info("활성 블랙리스트가 없습니다.")

    # 탭 5: 공지사항
    with tab5:
        st.markdown("### 📢 공지사항 통계")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("전체 공지사항", f"{stats['announcements']['total']}건")

        with col2:
            st.metric("상단 고정", f"{stats['announcements']['pinned']}건")

        # 공지사항 목록
        st.markdown("#### 📋 공지사항 목록")

        announcements_list = db.list_announcements(is_active=True)

        if announcements_list:
            category_badge = {"공지": "📢", "안내": "ℹ️", "이벤트": "🎉"}

            for ann in announcements_list:
                badge = (
                    category_badge[ann["category"]]
                    if ann and "category" in ann and ann["category"] in category_badge
                    else "📢"
                )
                pin_indicator = (
                    " 📌" if ann and "is_pinned" in ann and ann["is_pinned"] else ""
                )

                with st.expander(f"{badge} {ann['title']}{pin_indicator}"):
                    st.markdown(ann["content"])

                    st.markdown(f"""
                    **카테고리**: {ann["category"] if ann and "category" in ann else "공지"}
                    **작성자**: {ann["author_name"] if ann and "author_name" in ann else "Unknown"}
                    **작성일시**: {ann["created_at"][:19] if ann and "created_at" in ann and ann["created_at"] else "N/A"}
                    **수정일시**: {ann["updated_at"] if ann and "updated_at" in ann and ann["updated_at"] else "없음"}
                    """)

        else:
            st.info("활성 공지사항이 없습니다.")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 대시보드 안내

    - **새로고침**: 최신 데이터로 업데이트
    - **실시간**: 현재 DB 상태 기준
    - **추이 기간**: 예약 추이 그래프 기간

    **액션**:
    - 마스터는 사용자 실패 횟수를 초기화할 수 있습니다
    - 각 탭에서 세부 정보를 확인하세요
    """)
