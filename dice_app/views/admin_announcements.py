#!/usr/bin/env python3
"""
관리자 공지사항 관리 페이지
"""

import streamlit as st
import database as db
import auth
from datetime import datetime


def show():
    """공지사항 관리 페이지 표시"""
    # 관리자 권한 확인
    auth.require_login(required_role="admin")

    user = auth.get_current_user()
    is_master = auth.is_master()

    st.title("📢 공지사항 관리")
    st.markdown("---")

    # 통계
    all_announcements = db.list_announcements(is_active=True)
    total_announcements = len(all_announcements)
    pinned_announcements = len([a for a in all_announcements if a.get("is_pinned")])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("전체 공지사항", f"{total_announcements}건")

    with col2:
        st.metric("상단 고정", f"{pinned_announcements}건")

    st.markdown("---")

    # 탭
    tab1, tab2, tab3 = st.tabs(
        ["📋 공지사항 목록", "➕ 공지사항 작성", "📜 비활성화 목록"]
    )

    # 탭 1: 공지사항 목록
    with tab1:
        st.markdown("### 📋 활성화된 공지사항")

        # 카테고리 필터
        category_filter = st.selectbox(
            "카테고리 필터", ["전체", "공지", "안내", "이벤트"]
        )

        st.markdown("---")

        # 필터링
        filtered_announcements = []
        for ann in all_announcements:
            if category_filter != "전체" and ann.get("category") != category_filter:
                continue
            filtered_announcements.append(ann)

        st.markdown(f"### 📋 공지사항 목록 ({len(filtered_announcements)}건)")

        if filtered_announcements:
            for ann in filtered_announcements:
                # 상단 고정 표시
                pinned_badge = "📌 상단고정 " if ann.get("is_pinned") else ""
                category_badge = {"공지": "📢", "안내": "ℹ️", "이벤트": "🎉"}

                badge = category_badge.get(ann.get("category"), "📢")

                with st.expander(f"{badge} {ann['title']}{pinned_badge}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # 미리보기
                        st.markdown("### 📋 내용 미리보기")
                        st.markdown(ann["content"])

                        st.markdown(f"""
                        **카테고리**: {ann.get("category", "공지")}
                        **작성자**: {ann.get("author_name", "Unknown")}
                        **작성일시**: {ann.get("created_at", "N/A")}
                        """)

                        if ann.get("updated_at"):
                            st.info(f"수정일시: {ann['updated_at']}")

                    with col2:
                        st.markdown("### 액션")

                        # 상단 고정 토글
                        if st.button(
                            "고정 해제" if ann.get("is_pinned") else "상단 고정",
                            key=f"toggle_pin_{ann['id']}",
                            use_container_width=True,
                        ):
                            try:
                                new_pinned = not ann.get("is_pinned")
                                db.update_announcement(ann["id"], is_pinned=new_pinned)
                                st.success("✓ 상태가 업데이트되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"업데이트 중 오류가 발생했습니다: {e}")

                        # 수정 버튼
                        if st.button(
                            "수정", key=f"edit_{ann['id']}", use_container_width=True
                        ):
                            st.session_state["edit_announcement_id"] = ann["id"]
                            st.rerun()

                        # 비활성화 버튼
                        if st.button(
                            "비활성화",
                            key=f"deactivate_{ann['id']}",
                            use_container_width=True,
                        ):
                            if st.confirm("정말 이 공지사항을 비활성화하시겠습니까?"):
                                try:
                                    db.update_announcement(ann["id"], is_active=0)
                                    st.success("✓ 비활성화되었습니다.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"비활성화 중 오류가 발생했습니다: {e}")

                        # 영구 삭제 버튼 (마스터만)
                        if is_master:
                            if st.button(
                                "영구 삭제",
                                key=f"delete_{ann['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    "정말 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
                                ):
                                    try:
                                        db.delete_announcement(ann["id"])
                                        st.success("✓ 영구 삭제되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"삭제 중 오류가 발생했습니다: {e}")
        else:
            st.info("활성화된 공지사항이 없습니다.")

    # 탭 2: 공지사항 작성
    with tab2:
        # 수정 모드 체크
        edit_mode = "edit_announcement_id" in st.session_state

        if edit_mode:
            announcement_id = st.session_state["edit_announcement_id"]
            ann = db.get_announcement_by_id(announcement_id)

            if ann:
                st.markdown(f"### ✏️ 공지사항 수정 (ID: {announcement_id})")
            else:
                st.error("공지사항을 찾을 수 없습니다.")
                st.session_state.pop("edit_announcement_id", None)
                st.rerun()
        else:
            st.markdown("### ➕ 공지사항 작성")
            ann = None

        col1, col2 = st.columns([1, 2])

        with col1:
            # 폼
            title = st.text_input(
                "제목",
                value=ann["title"] if ann else "",
                placeholder="공지사항 제목을 입력하세요",
                key="announcement_title",
            )

            category = st.selectbox(
                "카테고리",
                ["공지", "안내", "이벤트"],
                index=["공지", "안내", "이벤트"].index(ann.get("category", "공지"))
                if ann
                else 0,
                key="announcement_category",
            )

            is_pinned = st.checkbox(
                "상단 고정",
                value=ann.get("is_pinned", False) if ann else False,
                key="announcement_pinned",
            )

            st.markdown("### 📝 내용 (Markdown 지원)")

            content = st.text_area(
                "내용",
                value=ann.get("content", "") if ann else "",
                placeholder="공지사항 내용을 입력하세요...",
                height=200,
                key="announcement_content",
            )

            # Markdown 미리보기
            if content:
                st.markdown("### 👁️ 미리보기")
                st.markdown(content)

        with col2:
            st.markdown("### 💡 안내")

            st.markdown("""
            **카테고리**:
            - 📢 **공지**: 중요한 시스템 공지
            - ℹ️ **안내**: 사용자 안내사항
            - 🎉 **이벤트**: 이벤트 관련 정보

            **상단 고정**:
            - 상단 고정된 공지는 홈페이지 맨 위에 표시됩니다.
            - 여러 개가 고정될 경우 최신순으로 표시됩니다.

            **Markdown 지원**:
            - # 제목 (H1)
            - ## 소제목 (H2)
            - **굵은 텍스트**
            - *기울임 텍스트*
            - [링크](URL)
            - ```코드```

            **예시**:
            ```markdown
            # 새로운 기능 안내

            다음 기능이 추가되었습니다:
            - 기능 1
            - 기능 2

            **중요**: 3월 1일부터 적용됩니다.
            ```
            """)

        # 버튼 영역
        st.markdown("---")

        if edit_mode:
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

            with col_btn1:
                if st.button("취소", use_container_width=True):
                    st.session_state.pop("edit_announcement_id", None)
                    st.rerun()

            with col_btn2:
                if st.button("수정", type="primary", use_container_width=True):
                    if not title:
                        st.error("제목을 입력해주세요.")
                        return

                    if not content:
                        st.error("내용을 입력해주세요.")
                        return

                    try:
                        db.update_announcement(
                            announcement_id,
                            title=title,
                            category=category,
                            is_pinned=is_pinned,
                            content=content,
                        )

                        st.success("✓ 공지사항이 수정되었습니다.")
                        st.session_state.pop("edit_announcement_id", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"수정 중 오류가 발생했습니다: {e}")

            with col_btn3:
                if st.button("새로 작성", use_container_width=True):
                    st.session_state.pop("edit_announcement_id", None)
                    st.rerun()
        else:
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

            with col_btn2:
                if st.button("공지사항 등록", type="primary", use_container_width=True):
                    if not title:
                        st.error("제목을 입력해주세요.")
                        return

                    if not content:
                        st.error("내용을 입력해주세요.")
                        return

                    try:
                        announcement_id = db.create_announcement(
                            title=title,
                            category=category,
                            content=content,
                            is_pinned=is_pinned,
                            created_by=user["id"],
                        )

                        st.success(
                            f"✓ 공지사항이 등록되었습니다! (ID: {announcement_id})"
                        )
                        st.info("홈페이지에서 확인할 수 있습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 중 오류가 발생했습니다: {e}")

    # 탭 3: 비활성화 목록
    with tab3:
        st.markdown("### 📜 비활성화된 공지사항")

        # 비활성화 목록 불러오기
        inactive_announcements = db.list_announcements(is_active=False)

        if inactive_announcements:
            st.info(
                f"{len(inactive_announcements)}개의 비활성화된 공지사항이 있습니다."
            )

            for ann in inactive_announcements:
                category_badge = {"공지": "📢", "안내": "ℹ️", "이벤트": "🎉"}

                badge = category_badge.get(ann.get("category"), "📢")

                with st.expander(f"{badge} {ann['title']}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(ann["content"])

                        st.markdown(f"""
                        **카테고리**: {ann.get("category", "공지")}
                        **작성자**: {ann.get("author_name", "Unknown")}
                        **작성일시**: {ann.get("created_at", "N/A")}
                        """)

                    with col2:
                        # 활성화 버튼
                        if st.button(
                            "활성화",
                            key=f"activate_{ann['id']}",
                            use_container_width=True,
                        ):
                            try:
                                db.update_announcement(ann["id"], is_active=1)
                                st.success("✓ 활성화되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"활성화 중 오류가 발생했습니다: {e}")

                        # 영구 삭제 버튼 (마스터만)
                        if is_master:
                            if st.button(
                                "영구 삭제",
                                key=f"permanent_delete_{ann['id']}",
                                type="secondary",
                                use_container_width=True,
                            ):
                                if st.confirm(
                                    "정말 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
                                ):
                                    try:
                                        db.delete_announcement(ann["id"])
                                        st.success("✓ 영구 삭제되었습니다.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"삭제 중 오류가 발생했습니다: {e}")
        else:
            st.info("비활성화된 공지사항이 없습니다.")

    st.markdown("---")

    # 안내 메시지
    st.markdown("""
    ### 💡 관리자 안내

    - **활성화**: 홈페이지에서 보이는 공지사항
    - **비활성화**: 보이지 않는 공지사항 (보관용)
    - **상단 고정**: 홈페이지 맨 위에 표시
    - **Markdown**: 다양한 포맷 지원

    **공지사항 우선순위**:
    1. 상단 고정된 공지
    2. 최신 작성 공지
    3. 카테고리별 그룹화

    마스터 계정만 영구 삭제가 가능합니다.
    """)
