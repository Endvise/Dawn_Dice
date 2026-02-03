#!/usr/bin/env python3
"""
Excel Processing Utility Module
"""

import streamlit as st


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
