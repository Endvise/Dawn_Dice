#!/usr/bin/env python3
"""
Admin Announcements Management Page
"""

import streamlit as st
import database as db
import auth
from datetime import datetime


def show():
    """Show announcements management page"""
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("Announcements Management")
    st.markdown("---")

    # Statistics
    all_announcements = db.list_announcements(is_active=True)
    total_announcements = len(all_announcements)
    pinned_announcements = len([a for a in all_announcements if a.get("is_pinned")])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Announcements", f"{total_announcements}")

    with col2:
        st.metric("Pinned", f"{pinned_announcements}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(
        ["Announcements List", "Create Announcement", "Inactive List"]
    )

    # Tab 1: Announcements list
    with tab1:
        st.markdown("### Active Announcements")

        category_filter = st.selectbox(
            "Category Filter",
            ["All", "Notice", "Guide", "Event"],
            key="announcement_category_filter",
        )

        st.markdown("---")

        filtered_announcements = []
        for ann in all_announcements:
            if category_filter != "All" and ann.get("category") != category_filter:
                continue
            filtered_announcements.append(ann)

        st.markdown(f"### Announcements ({len(filtered_announcements)})")

        if filtered_announcements:
            for ann in filtered_announcements:
                pinned_badge = "📌 Pinned " if ann.get("is_pinned") else ""
                category_badge = {
                    "notice": "📢",
                    "guide": "ℹ️",
                    "event": "🎉",
                    "공지": "📢",
                    "안내": "ℹ️",
                    "이벤트": "🎉",
                }

                badge = category_badge.get(ann.get("category"), "📢")

                with st.expander(f"{badge} {ann['title']}{pinned_badge}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown("### Preview")
                        st.markdown(ann["content"])

                        st.markdown(f"""
                        **Category**: {ann.get("category", "notice")}
                        **Author**: {ann.get("author_name", "Unknown")}
                        **Created At**: {ann.get("created_at", "N/A")}
                        """)

                        if ann.get("updated_at"):
                            st.info(f"Updated at: {ann['updated_at']}")

                    with col2:
                        st.markdown("### Actions")

                        if st.button(
                            "Unpin" if ann.get("is_pinned") else "Pin to Top",
                            key=f"toggle_pin_{ann['id']}",
                            use_container_width=True,
                        ):
                            try:
                                new_pinned = not ann.get("is_pinned")
                                db.update_announcement(ann["id"], is_pinned=new_pinned)
                                st.success("Status updated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating: {e}")

                        if st.button(
                            "Edit", key=f"edit_{ann['id']}", use_container_width=True
                        ):
                            st.session_state["edit_announcement_id"] = ann["id"]
                            st.rerun()

                        if st.button(
                            "Deactivate",
                            key=f"deactivate_{ann['id']}",
                            use_container_width=True,
                        ):
                            if st.confirm("Deactivate this announcement?"):
                                try:
                                    db.update_announcement(ann["id"], is_active=0)
                                    st.success("Deactivated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deactivating: {e}")

                        if is_master:
                            if st.button(
                                "Delete Permanently",
                                key=f"delete_{ann['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    "Delete permanently? This cannot be undone."
                                ):
                                    try:
                                        db.delete_announcement(ann["id"])
                                        st.success("Permanently deleted.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
        else:
            st.info("No active announcements.")

    # Tab 2: Create announcement
    with tab2:
        edit_mode = "edit_announcement_id" in st.session_state

        if edit_mode:
            announcement_id = st.session_state["edit_announcement_id"]
            ann = db.get_announcement_by_id(announcement_id)

            if ann:
                st.markdown(f"### Edit Announcement (ID: {announcement_id})")
            else:
                st.error("Announcement not found.")
                st.session_state.pop("edit_announcement_id", None)
                st.rerun()
        else:
            st.markdown("### Create Announcement")
            ann = None

        col1, col2 = st.columns([1, 2])

        with col1:
            title = st.text_input(
                "Title",
                value=ann["title"] if ann else "",
                placeholder="Enter announcement title",
                key="announcement_title",
            )

            category = st.selectbox(
                "Category",
                ["notice", "guide", "event"],
                index=["notice", "guide", "event"].index(ann.get("category", "notice"))
                if ann
                else 0,
                key="announcement_category",
            )

            is_pinned = st.checkbox(
                "Pin to Top",
                value=ann.get("is_pinned", False) if ann else False,
                key="announcement_pinned",
            )

            st.markdown("### Content (Markdown supported)")

            content = st.text_area(
                "Content",
                value=ann.get("content", "") if ann else "",
                placeholder="Enter announcement content...",
                height=200,
                key="announcement_content",
            )

            if content:
                st.markdown("### Preview")
                st.markdown(content)

        with col2:
            st.markdown("### Guide")

            st.markdown("""
            **Categories:**
            - 📢 **Notice**: Important system announcements
            - ℹ️ **Guide**: User guides
            - 🎉 **Event**: Event information

            **Pin to Top:**
            - Pinned announcements appear at the top of the homepage
            - Multiple pinned items show in reverse chronological order

            **Markdown Support:**
            - # Heading (H1)
            - ## Subheading (H2)
            - **Bold text**
            - *Italic text*
            - [Link](URL)
            - ```code```

            **Example:**
            ```markdown
            # New Feature Guide

            The following features have been added:
            - Feature 1
            - Feature 2

            **Important**: Effective from March 1st.
            ```
            """)

        st.markdown("---")

        if edit_mode:
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

            with col_btn1:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.pop("edit_announcement_id", None)
                    st.rerun()

            with col_btn2:
                if st.button("Update", type="primary", use_container_width=True):
                    if not title:
                        st.error("Enter title.")
                        return

                    if not content:
                        st.error("Enter content.")
                        return

                    try:
                        db.update_announcement(
                            announcement_id,
                            title=title,
                            category=category,
                            is_pinned=is_pinned,
                            content=content,
                        )

                        st.success("Announcement updated.")
                        st.session_state.pop("edit_announcement_id", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating: {e}")

            with col_btn3:
                if st.button("New", use_container_width=True):
                    st.session_state.pop("edit_announcement_id", None)
                    st.rerun()
        else:
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

            with col_btn2:
                if st.button("Publish", type="primary", use_container_width=True):
                    if not title:
                        st.error("Enter title.")
                        return

                    if not content:
                        st.error("Enter content.")
                        return

                    try:
                        announcement_id = db.create_announcement(
                            title=title,
                            category=category,
                            content=content,
                            is_pinned=is_pinned,
                            created_by=user["id"],
                        )

                        st.success(f"Announcement published! (ID: {announcement_id})")
                        st.info("Check on the homepage.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error publishing: {e}")

    # Tab 3: Inactive list
    with tab3:
        st.markdown("### Inactive Announcements")

        inactive_announcements = db.list_announcements(is_active=False)

        if inactive_announcements:
            st.info(f"{len(inactive_announcements)} inactive announcements.")

            for ann in inactive_announcements:
                category_badge = {
                    "notice": "📢",
                    "guide": "ℹ️",
                    "event": "🎉",
                    "공지": "📢",
                    "안내": "ℹ️",
                    "이벤트": "🎉",
                }

                badge = category_badge.get(ann.get("category"), "📢")

                with st.expander(f"{badge} {ann['title']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(ann["content"])

                        st.markdown(f"""
                        **Category**: {ann.get("category", "notice")}
                        **Author**: {ann.get("author_name", "Unknown")}
                        **Created At**: {ann.get("created_at", "N/A")}
                        """)

                    with col2:
                        if st.button(
                            "Activate",
                            key=f"activate_{ann['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.update_announcement(ann["id"], is_active=1)
                                st.success("Activated.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error activating: {e}")

                        if is_master:
                            if st.button(
                                "Delete Permanently",
                                key=f"permanent_delete_{ann['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    "Delete permanently? This cannot be undone."
                                ):
                                    try:
                                        db.delete_announcement(ann["id"])
                                        st.success("Permanently deleted.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting: {e}")
        else:
            st.info("No inactive announcements.")

    st.markdown("---")

    st.markdown("""
    ### Admin Guide

    - **Active**: Visible on homepage
    - **Inactive**: Hidden (archived)
    - **Pin to Top**: Shows at top of homepage
    - **Markdown**: Supports various formats

    **Announcement Priority:**
    1. Pinned announcements
    2. Most recent
    3. Grouped by category

    Only master accounts can permanently delete.
    """)
