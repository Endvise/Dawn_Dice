#!/usr/bin/env python3
"""
Admin Dashboard Page (Real-time Statistics)
"""

import streamlit as st
import database as db
import auth
from database import execute_query
from datetime import datetime, timedelta


def get_dashboard_stats() -> dict:
    """Return dashboard statistics."""
    # User statistics
    total_users = len(db.list_users())
    active_users = len(db.list_users(is_active=True))
    admin_users = len(db.list_users(role="admin"))

    # Reservation statistics
    all_reservations = db.list_reservations()

    pending = len([r for r in all_reservations if r["status"] == "pending"])
    approved = len([r for r in all_reservations if r["status"] == "approved"])
    rejected = len([r for r in all_reservations if r["status"] == "rejected"])
    cancelled = len([r for r in all_reservations if r["status"] == "cancelled"])
    waitlisted = len([r for r in all_reservations if r["status"] == "waitlisted"])

    # Blacklist statistics
    blacklist = db.list_blacklist(is_active=True)

    # Participant statistics
    participants = db.list_participants()
    completed = len([p for p in participants if p.get("completed")])
    confirmed = len([p for p in participants if p.get("confirmed")])

    # Announcement statistics
    announcements = db.list_announcements(is_active=True)
    pinned = len([a for a in announcements if a.get("is_pinned")])

    # Total participants (existing + approved reservations)
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
    """Return reservation trend."""
    trend = []

    for i in range(days):
        date = datetime.now() - timedelta(days=days - 1 - i)
        date_str = date.strftime("%Y-%m-%d")

        result = execute_query(
            """
            SELECT COUNT(*) as count
            FROM reservations
            WHERE DATE(created_at) = ?
            """,
            (date_str,),
            fetch="one",
        )

        if result and isinstance(result, dict) and "count" in result:
            count = result["count"]
        elif result and hasattr(result, "__getitem__"):
            try:
                count = result[0]
            except (IndexError, KeyError, TypeError):
                count = 0
        else:
            count = 0
        trend.append({"date": date_str, "count": count})

    return trend


def show():
    """Show dashboard page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Dashboard")
    st.markdown("---")

    if st.button("Refresh", use_container_width=True):
        st.rerun()

    col1, col2 = st.columns([1, 2])

    with col1:
        trend_days = st.selectbox(
            "Trend Period", [7, 14, 30], index=0, key="dashboard_trend_days"
        )

    with col2:
        st.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    stats = get_dashboard_stats()

    st.markdown("## Key Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if stats["overall"]["is_full"]:
            st.error("Full - No Reservations")
        else:
            st.success("Open for Reservations")

        st.metric(
            "Participants",
            f"{stats['overall']['total_participants']} / {stats['overall']['max_participants']}",
            delta=f"{stats['overall']['waitlist_count']} waiting",
            delta_color="normal" if stats["overall"]["waitlist_count"] > 0 else "off",
        )

    with col2:
        st.metric("Pending", f"{stats['reservations']['pending']}")

    with col3:
        st.metric("Approved", f"{stats['reservations']['approved']}")

    with col4:
        st.metric("Waitlist", f"{stats['reservations']['waitlisted']}")

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Users", "Reservations", "Participants", "Blacklist", "Announcements"]
    )

    with tab1:
        st.markdown("### User Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Users", f"{stats['users']['total']}")

        with col2:
            st.metric("Active Users", f"{stats['users']['active']}")

        with col3:
            st.metric("Admins", f"{stats['users']['admin']}")

        st.markdown("#### User List")

        users_list = db.list_users()

        if users_list:
            for user_data in users_list:
                role_badge = {"master": "👑", "admin": "🛡️", "user": "👤"}

                badge = role_badge.get(user_data["role"], "👤")

                with st.expander(
                    f"{badge} {user_data.get('username', user_data.get('commander_id', 'Unknown'))} - {user_data.get('nickname', 'Unknown')}"
                ):
                    st.markdown(f"""
                    **Role**: {user_data.get("role", "Unknown")}
                    **Server**: {user_data.get("server", "N/A")}
                    **Alliance**: {user_data.get("alliance", "None") if user_data.get("alliance") else "None"}
                    **Created At**: {user_data.get("created_at", "N/A")}
                    **Last Login**: {user_data.get("last_login", "N/A") if user_data.get("last_login") else "None"}
                    **Status**: {"Active" if user_data.get("is_active") else "Inactive"}
                    """)

                    if user_data.get("failed_attempts", 0) > 0:
                        st.warning(f"Login failures: {user_data['failed_attempts']}")

                    if user_data.get("failed_attempts", 0) > 0 and is_master:
                        if st.button(
                            "Reset Failures",
                            key=f"reset_failed_{user_data['id']}",
                            use_container_width=True,
                        ):
                            db.update_user(user_data["id"], failed_attempts=0)
                            st.success("Reset.")
                            st.rerun()

        else:
            st.info("No registered users.")

    with tab2:
        st.markdown("### Reservation Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total", f"{stats['reservations']['total']}")

        with col2:
            st.metric("Pending", f"{stats['reservations']['pending']}")

        with col3:
            st.metric(
                "Completed",
                f"{stats['reservations']['approved'] + stats['reservations']['rejected']}",
            )

        st.markdown("#### Reservation Status Distribution")

        status_data = [
            {"Status": "Pending", "Count": stats["reservations"]["pending"]},
            {"Status": "Approved", "Count": stats["reservations"]["approved"]},
            {"Status": "Rejected", "Count": stats["reservations"]["rejected"]},
            {"Status": "Cancelled", "Count": stats["reservations"]["cancelled"]},
            {"Status": "Waitlist", "Count": stats["reservations"]["waitlisted"]},
        ]

        for data in status_data:
            color = {
                "Pending": "🟡",
                "Approved": "🟢",
                "Rejected": "🔴",
                "Cancelled": "⚪",
                "Waitlist": "🔵",
            }

            badge = color.get(data["Status"], "❓")
            percentage = (
                (data["Count"] / stats["reservations"]["total"] * 100)
                if stats["reservations"]["total"] > 0
                else 0
            )

            st.markdown(f"""
            **{badge} {data["Status"]}**: {data["Count"]} ({percentage:.1f}%)
            """)

        st.markdown("---")
        st.markdown(f"#### Recent {trend_days} Day Trend")

        trend = get_reservation_trend(trend_days)

        if trend:
            import pandas as pd

            df = pd.DataFrame(trend)
            st.line_chart(df.set_index("date"))
        else:
            st.info("No data.")

    with tab3:
        st.markdown("### Participant Statistics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total", f"{stats['participants']['total']}")

        with col2:
            st.metric("Completed", f"{stats['participants']['completed']}")

        with col3:
            st.metric("Confirmed", f"{stats['participants']['confirmed']}")

        st.markdown("#### Participants by Event")

        participants_list = db.list_participants()

        if participants_list:
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

            for event_name, data in sorted(event_stats.items()):
                with st.expander(f"🎉 {event_name}"):
                    st.markdown(f"""
                    **Total**: {data["total"]}
                    **Completed**: {data["completed"]}
                    **Confirmed**: {data["confirmed"]}
                    """)

        else:
            st.info("No participant data.")

    with tab4:
        st.markdown("### Blacklist Statistics")

        st.metric("Active Blacklist", f"{stats['blacklist']['total']}")

        st.markdown("#### Blacklist List")

        blacklist_list = db.list_blacklist(is_active=True)

        if blacklist_list:
            for bl in blacklist_list:
                with st.expander(
                    f"🚫 {bl['commander_id']} - {bl['nickname'] if bl and 'nickname' in bl else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **Commander ID**: {bl["commander_id"]}
                    **Nickname**: {bl["nickname"] if bl and "nickname" in bl else "Unknown"}
                    **Reason**: {bl["reason"] if bl and "reason" in bl else "N/A"}
                    **Added At**: {bl["added_at"]}
                    """)

        else:
            st.info("No active blacklist entries.")

    with tab5:
        st.markdown("### Announcement Statistics")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total", f"{stats['announcements']['total']}")

        with col2:
            st.metric("Pinned", f"{stats['announcements']['pinned']}")

        st.markdown("#### Announcement List")

        announcements_list = db.list_announcements(is_active=True)

        if announcements_list:
            category_badge = {
                "notice": "📢",
                "guide": "ℹ️",
                "event": "🎉",
                "공지": "📢",
                "안내": "ℹ️",
                "이벤트": "🎉",
            }

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
                    **Category**: {ann["category"] if ann and "category" in ann else "notice"}
                    **Author**: {ann["author_name"] if ann and "author_name" in ann else "Unknown"}
                    **Created At**: {ann["created_at"][:19] if ann and "created_at" in ann and ann["created_at"] else "N/A"}
                    **Updated At**: {ann["updated_at"] if ann and "updated_at" in ann and ann["updated_at"] else "None"}
                    """)

        else:
            st.info("No active announcements.")

    st.markdown("---")

    st.markdown("""
    ### Dashboard Guide

    - **Refresh**: Update with latest data
    - **Real-time**: Based on current DB state
    - **Trend Period**: Reservation trend graph period

    **Actions:**
    - Masters can reset user failure counts
    - Check details in each tab
    """)
