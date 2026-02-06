#!/usr/bin/env python3
"""
Utility Module
- Excel Processing
- Timezone Management
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Dict, List


# Available timezones
TIMEZONE_OPTIONS = [
    ("UTC", "UTC", 0),
    ("🇰🇷 Korea (KST)", "Asia/Seoul", 9),
    ("🇯🇵 Japan (JST)", "Asia/Tokyo", 9),
    ("🇨🇳 China (CST)", "Asia/Shanghai", 8),
    ("🇭🇰 Hong Kong (HKT)", "Asia/Hong_Kong", 8),
    ("🇸🇬 Singapore (SGT)", "Asia/Singapore", 8),
    ("🇬🇧 UK (GMT)", "Europe/London", 0),
    ("🇪🇺 Europe (CET)", "Europe/Paris", 1),
    ("🇪🇺 Europe (EET)", "Europe/Helsinki", 2),
    ("🇺🇸 US Pacific (PST)", "America/Los_Angeles", -8),
    ("🇺🇸 US Mountain (MST)", "America/Denver", -7),
    ("🇺🇸 US Central (CST)", "America/Chicago", -6),
    ("🇺🇸 US Eastern (EST)", "America/New_York", -5),
    ("🇨🇦 Canada (EST)", "America/Toronto", -5),
    ("🇦🇺 Australia (AEST)", "Australia/Sydney", 10),
    ("🇳🇿 New Zealand (NZST)", "Pacific/Auckland", 13),
    ("🇧🇷 Brazil (BRT)", "America/Sao_Paulo", -3),
    ("🇮🇳 India (IST)", "Asia/Kolkata", 5.5),
    ("🇧🇩 Bangladesh (BST)", "Asia/Dhaka", 6),
    ("🇹🇭 Thailand (ICT)", "Asia/Bangkok", 7),
    ("🇻🇳 Vietnam (ICT)", "Asia/Ho_Chi_Minh", 7),
    ("🇵🇭 Philippines (PHT)", "Asia/Manila", 8),
    ("🇲🇾 Malaysia (MYT)", "Asia/Kuala_Lumpur", 8),
    ("🇮🇩 Indonesia (WIB)", "Asia/Jakarta", 7),
]


def get_timezone_offset(timezone_str: str) -> float:
    """Get UTC offset for a timezone string."""
    for name, tz, offset in TIMEZONE_OPTIONS:
        if tz == timezone_str:
            return offset
    return 0  # Default to UTC


def parse_utc_time(dt_str: str) -> Optional[datetime]:
    """Parse a datetime string stored in UTC format."""
    if not dt_str:
        return None
    try:
        # Handle ISO format with Z or +00:00
        dt_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        # Make it timezone-aware if not already
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def format_timezone_time(
    dt: datetime, timezone_str: str, format_str: str = "%Y-%m-%d %H:%M"
) -> str:
    """Convert UTC datetime to specified timezone and format."""
    if dt is None:
        return "N/A"
    try:
        offset_hours = get_timezone_offset(timezone_str)
        # Create timezone with offset
        tz = timezone(timedelta(hours=offset_hours))
        local_dt = dt.astimezone(tz)
        return local_dt.strftime(format_str)
    except (TypeError, ValueError):
        return str(dt)


def format_utc_to_timezone(
    dt_str: str, timezone_str: str, format_str: str = "%Y-%m-%d %H:%M"
) -> str:
    """Convert UTC datetime string to specified timezone."""
    dt = parse_utc_time(dt_str)
    return format_timezone_time(dt, timezone_str, format_str) if dt else "N/A"


def get_timezone_display_name(timezone_str: str) -> str:
    """Get display name for a timezone."""
    for name, tz, offset in TIMEZONE_OPTIONS:
        if tz == timezone_str:
            return name.split(" ")[0] if " " in name else name
    return "🌍"


def show_timezone_selector(key: str = "timezone_selector") -> str:
    """
    Show timezone selector in Streamlit sidebar.
    Returns the selected timezone string.
    """
    # Initialize timezone in session state if not set
    timezone_key = f"selected_{key}"
    if timezone_key not in st.session_state:
        st.session_state[timezone_key] = "UTC"

    # Get current selection
    current_tz = st.session_state[timezone_key]

    # Create options list
    options = [f"{name}" for name, tz, offset in TIMEZONE_OPTIONS]
    tz_values = [tz for name, tz, offset in TIMEZONE_OPTIONS]

    # Find current index
    try:
        current_idx = tz_values.index(current_tz)
    except ValueError:
        current_idx = 0  # Default to UTC

    # Show selector
    selected = st.selectbox(
        "🌍 Timezone",
        options=options,
        index=current_idx,
        key=f"select_{key}",
        help="Select your timezone to see event times in your local time",
    )

    # Update session state
    if selected:
        for name, tz, offset in TIMEZONE_OPTIONS:
            if name == selected:
                st.session_state[timezone_key] = tz
                break

    return st.session_state[timezone_key]


def format_event_time(dt_str: str, timezone_key: str = "timezone_selector") -> str:
    """Format event time string to user's selected timezone."""
    tz = st.session_state.get(f"selected_{timezone_key}", "UTC")
    return format_utc_to_timezone(dt_str, tz)


def show_timezone_info(dt_str: str, timezone_key: str = "timezone_selector") -> str:
    """Show formatted time with timezone info."""
    if not dt_str:
        return "N/A"
    tz = st.session_state.get(f"selected_{timezone_key}", "UTC")
    local_time = format_utc_to_timezone(dt_str, tz)
    display_name = get_timezone_display_name(tz)
    return f"{local_time} ({display_name})"


def map_excel_columns(headers):
    """
    Auto-map Excel columns to database fields
    - Priority: commander_id, nickname, affiliation, alliance, etc.
    """
    mapping = {}

    for idx, header in enumerate(headers):
        header_str = str(header).lower().strip()

        # Commander ID related columns (high priority)
        if any(
            keyword in header_str
            for keyword in [
                "commander_id",
                "commander",
                "number",
                "id",
                "igg_id",
                "igg id",
            ]
        ):
            mapping["commander_id"] = idx

        # General column mapping
        if any(keyword in header_str for keyword in ["nickname", "name"]):
            if "commander_id" not in mapping:
                mapping["nickname"] = idx
        elif any(keyword in header_str for keyword in ["affiliation", "guild"]):
            mapping["affiliation"] = idx
        elif any(keyword in header_str for keyword in ["alliance"]):
            mapping["alliance"] = idx
        elif any(keyword in header_str for keyword in ["notes", "comment"]):
            mapping["notes"] = idx
        elif any(keyword in header_str for keyword in ["wait", "wait_confirmed"]):
            mapping["wait_confirmed"] = idx
        elif any(keyword in header_str for keyword in ["confirm", "confirmed"]):
            mapping["confirmed"] = idx
        elif any(keyword in header_str for keyword in ["completed", "complete"]):
            mapping["completed"] = idx
        elif any(keyword in header_str for keyword in ["record", "participation"]):
            mapping["participation_record"] = idx

        # Default: first column is commander_id
        if idx == 0 and "commander_id" not in mapping:
            mapping["commander_id"] = idx

    return mapping


def extract_row_data(row, headers, column_mapping):
    """
    Extract row data and map to database fields
    """
    row_data = {}

    for field, col_idx in column_mapping.items():
        if col_idx < len(row) and row[col_idx] is not None:
            cell_value = str(row[col_idx]).strip() if row[col_idx] is not None else None
            row_data[field] = cell_value

    return row_data


def display_column_mapping_info(column_mapping, headers):
    """
    Display column mapping information
    """
    if column_mapping:
        st.markdown("### 🗂️ Detected Column Mapping")
        for field, idx in column_mapping.items():
            col_name = headers[idx] if idx < len(headers) else "N/A"
            st.markdown(f"- **{field}**: `{col_name}` (Column {idx + 1})")


def display_preview_data(rows):
    """
    Display preview data
    """
    if rows:
        st.markdown("### 📋 Preview (First 5 records)")
        for preview_row in rows[:5]:
            commander_id = preview_row.get("commander_id", "N/A")
            nickname = preview_row.get("nickname", "N/A")
            st.text(f"- {nickname}: {commander_id}")

        st.info("💡 Columns are automatically detected and mapped.")
