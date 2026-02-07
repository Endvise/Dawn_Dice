#!/usr/bin/env python3
"""
Admin Dashboard Page (Real-time Statistics)
"""

import streamlit as st
import database as db
import auth
import utils
from datetime import datetime, timedelta


def format_dashboard_time() -> str:
    """Format current time with user's timezone."""
    timezone_key = "timezone_selector"
    tz = st.session_state.get(f"selected_{timezone_key}", "UTC")
    offset = utils.get_timezone_offset(tz)
    from datetime import timezone as tzinfo, timedelta as td

    tz_info = tzinfo(td(hours=offset))
    return datetime.now(tz_info).strftime("%Y-%m-%d %H:%M:%S")


def get_dashboard_stats() -> dict:
    """Return dashboard statistics."""
    # User statistics
    total_users = len(db.list_users())
    active_users = len(db.list_users(is_active=True))
    admin_users = len(db.list_admins(role="admin"))

    # Get current active session
    active_session = db.get_active_session()
    current_session_name = (
        active_session.get("session_name") if active_session else None
    )

    # Reservation statistics (no status field in Supabase schema)
    all_reservations = (
        db.list_reservations(event_name=current_session_name)
        if current_session_name
        else []
    )

    approved = len(all_reservations)

    # Blacklist statistics (is_active removed from params)
    blacklist = db.list_blacklist()

    # Participant statistics - 현재 활성화된 세션 기준
    if current_session_name:
        participants = db.list_participants(current_session_name)
    else:
        participants = []

    total_participants = len(participants)
    completed = len([p for p in participants if p.get("completed")])
    confirmed = len([p for p in participants if p.get("confirmed")])

    # Announcement statistics
    announcements = db.list_announcements(is_active=True)
    pinned = len([a for a in announcements if a.get("is_pinned")])

    # Overall statistics
    max_participants = (
        active_session.get("max_participants", 180) if active_session else 180
    )

    return {
        "users": {"total": total_users, "active": active_users, "admin": admin_users},
        "reservations": {
            "total": len(all_reservations),
            "pending": 0,
            "approved": approved,
            "rejected": 0,
            "cancelled": 0,
            "waitlisted": 0,
        },
        "blacklist": {"total": len(blacklist)},
        "participants": {
            "total": total_participants,
            "completed": completed,
            "confirmed": confirmed,
        },
        "announcements": {"total": len(announcements), "pinned": pinned},
        "overall": {
            "current_session": current_session_name,
            "total_participants": total_participants,
            "max_participants": max_participants,
            "is_full": total_participants >= max_participants,
            "waitlist_count": 0,
        },
    }


def get_reservation_trend(days: int = 7) -> list:
    """Return reservation trend."""
    # Get all reservations
    all_reservations = db.list_reservations()

    trend = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days - 1 - i)
        date_str = date.strftime("%Y-%m-%d")

        # Filter by date in Python (Supabase doesn't support DATE() function)
        count = len(
            [
                r
                for r in all_reservations
                if r.get("created_at") and r["created_at"][:10] == date_str
            ]
        )

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
        st.info(f"Last updated: {format_dashboard_time()}")

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

    # Session Check-in Status Section
    render_session_checkin_status()

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
                # Users table only contains regular users, admins are in separate table
                badge = "👤"

                with st.expander(
                    f"{badge} {user_data.get('commander_number', 'Unknown')} - {user_data.get('nickname', 'Unknown')}"
                ):
                    st.markdown(f"""
                    **Role**: User
                    **Server**: {user_data.get("server", "N/A")}
                    **Alliance**: {user_data.get("alliance", "None") if user_data.get("alliance") else "None"}
                    **Created At**: {user_data.get("created_at", "N/A")}
                    **Status**: {"Active" if user_data.get("is_active") else "Inactive"}
                    """)

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

        blacklist_list = db.list_blacklist()

        if blacklist_list:
            for bl in blacklist_list:
                with st.expander(
                    f"🚫 {bl['commander_number']} - {bl['nickname'] if bl and 'nickname' in bl else 'Unknown'}"
                ):
                    st.markdown(f"""
                    **Commander ID**: {bl["commander_number"]}
                    **Nickname**: {bl["nickname"] if bl and "nickname" in bl else "Unknown"}
                    **Reason**: {bl["reason"] if bl and "reason" in bl else "N/A"}
                    **Created At**: {bl["created_at"]}
                    **Expires At**: {bl["expires_at"] if bl and "expires_at" in bl else "Never"}
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

    # Admin actions section
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔐 Change My Password", use_container_width=True):
            st.session_state["page"] = "admin_management"
            st.rerun()

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


def render_session_checkin_status():
    """Render session check-in status section in dashboard."""
    # Get active session
    active_session = db.get_active_session()
    if not active_session:
        st.markdown("### 🎯 Session Check-in Status")
        st.info("No active session. Create a session first.")
        return

    session_id = str(active_session["id"])
    session_name = active_session.get(
        "session_name", f"Session {active_session.get('session_number', '?')}"
    )

    st.markdown(f"### 🎯 Session Check-in Status - {session_name}")

    # Get check-in stats
    stats = db.get_session_check_stats(session_id)

    if stats["total"] == 0:
        st.info("No participants in this session yet.")
        return

    # Display metrics in a compact way
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", stats["total"])

    with col2:
        st.metric(
            "Re-confirmed",
            f"{stats['re_confirmed']} ({stats['re_confirmed_percent']}%)",
            delta_color="normal",
        )

    with col3:
        st.metric(
            "Alliance Entry",
            f"{stats['alliance_entry']} ({stats['alliance_entry_percent']}%)",
            delta_color="normal",
        )

    with col4:
        st.metric(
            "Dice Purchased",
            f"{stats['dice_purchased']} ({stats['dice_purchased_percent']}%)",
            delta_color="normal",
        )

    # Progress bar
    st.markdown("**Re-confirmed Progress**")
    st.progress(stats["re_confirmed_percent"] / 100)

    # Link to check-in management
    if st.button("📋 Open Check-in Management", use_container_width=True):
        st.session_state["page"] = "🎯 Session Check-in"
        st.rerun()
