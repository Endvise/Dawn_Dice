#!/usr/bin/env python3
"""
My Reservations page
"""

import streamlit as st
import database as db
import auth


def show():
    """Show my reservations page"""
    auth.require_login()

    user = auth.get_current_user()

    # user가 None인 경우 처리
    if not user:
        st.error("User information not found. Please log in again.")
        return

    st.title("My Reservations")
    st.markdown("---")

    # Get my reservations
    my_reservations = db.list_reservations(user_id=user["id"])

    if not my_reservations:
        st.info("No reservations found.")
        return

    # Show each reservation with status
    for res in my_reservations:
        # Status display - handle missing status field
        status = res.get(
            "status", "approved"
        )  # Default to approved for simple reservations
        waitlist_order = res.get("waitlist_order", 0)

        if status == "pending":
            status_icon = "⏳"
            status_text = "Pending"
        elif status == "rejected":
            status_icon = "❌"
            status_text = "Rejected"
        elif status == "cancelled":
            status_icon = "⚪"
            status_text = "Cancelled"
        elif status == "waitlisted":
            status_icon = "🔵"
            status_text = f"Waitlisted (Order: {waitlist_order})"
        else:
            status_icon = "✅"
            status_text = "Confirmed"

        # Date
        created_at = res["created_at"][:10] if res.get("created_at") else ""

        # Simple card display
        st.markdown(
            f"""
<div style="padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 10px;">
    <strong>{status_icon} {status_text}</strong> &nbsp;|&nbsp; {created_at}
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Legend
    st.markdown("""
**Reservation Status Guide**
- **Approved**: Reservation confirmed
- **Pending**: Waiting for admin approval
- **Rejected**: Reservation rejected by admin
- **Cancelled**: Cancelled by user
- **Waitlisted**: Added to waitlist due to full capacity
""")
