import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _normalize_text(value):
    """Normalize text values from Excel by stripping whitespace and blanking missing values."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _extract_sheet_count(sheet_name):
    """Extract the material-group count from a processed sheet name like '3mgs'."""
    match = re.search(r"(\d+)\s*mgs", str(sheet_name).strip().lower())
    if match:
        return int(match.group(1))
    return None


def _get_count_options(xlsx_path):
    """Return the set of available material-group counts defined in the workbook sheets."""
    if not os.path.exists(xlsx_path):
        return []

    xls = pd.ExcelFile(xlsx_path)
    counts = []
    for sheet_name in xls.sheet_names:
        count = _extract_sheet_count(sheet_name)
        if count is not None and count not in counts:
            counts.append(count)
    return sorted(counts)


def _load_events_for_count(xlsx_path, count):
    """Load every event grouped by a selected material-group count."""
    sheet_name = f"{count}mgs"
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    lower_cols = {str(c).strip().lower(): c for c in df.columns}
    event_col = lower_cols.get("serviceeventcode")
    group_col = lower_cols.get("materialgroup")
    desc_col = lower_cols.get("materialgroupdescription")

    if event_col is None or group_col is None or desc_col is None:
        return []

    filtered_df = df[[event_col, group_col, desc_col]].copy()
    filtered_df.columns = ["event", "group", "description"]
    filtered_df["event"] = filtered_df["event"].map(_normalize_text)
    filtered_df["group"] = filtered_df["group"].map(_normalize_text)
    filtered_df["description"] = filtered_df["description"].map(_normalize_text)
    filtered_df = filtered_df[(filtered_df["event"] != "") & (filtered_df["group"] != "")].copy()

    grouped = {}
    for _, row in filtered_df.iterrows():
        event = row["event"]
        group = row["group"]
        description = row["description"]

        grouped.setdefault(event, {})
        if group not in grouped[event]:
            grouped[event][group] = description

    result = []
    for event_name, materials in sorted(grouped.items()):
        result.append(
            {
                "event": event_name,
                "material_groups": [
                    {"id": group_id, "description": description}
                    for group_id, description in materials.items()
                ],
            }
        )

    return result


def _load_selected_event_data(xlsx_path, count, selected_event):
    """Load the detailed rows for the selected event and material-group count."""
    sheet_name = f"{count}mgs"
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    lower_cols = {str(c).strip().lower(): c for c in df.columns}
    event_col = lower_cols.get("serviceeventcode")
    item_col = lower_cols.get("itemnumber")
    material_name_col = lower_cols.get("materialname")
    group_col = lower_cols.get("materialgroup")
    group_desc_col = lower_cols.get("materialgroupdescription")

    required_cols = [col for col in [event_col, item_col, material_name_col, group_col, group_desc_col] if col is not None]
    if not required_cols or event_col is None or group_col is None or group_desc_col is None:
        return pd.DataFrame()

    filtered_df = df[required_cols].copy()
    filtered_df.columns = ["Service Event Code", "Material ID", "Material Name", "Material Group ID", "Material Group Description"]

    filtered_df["Service Event Code"] = filtered_df["Service Event Code"].map(_normalize_text)
    filtered_df["Material ID"] = filtered_df["Material ID"].map(_normalize_text)
    filtered_df["Material Name"] = filtered_df["Material Name"].map(_normalize_text)
    filtered_df["Material Group ID"] = filtered_df["Material Group ID"].map(_normalize_text)
    filtered_df["Material Group Description"] = filtered_df["Material Group Description"].map(_normalize_text)

    if len(filtered_df.columns) < 5:
        return pd.DataFrame()

    return filtered_df[filtered_df["Service Event Code"] == selected_event].reset_index(drop=True)


def _set_selected_event(event_name):
    """Set the currently selected service event in session state."""
    st.session_state["selected_event"] = event_name
    st.session_state.pop(f"material_group_selection_{event_name}", None)


def _toggle_selected_group(selected_event, group_id):
    """Toggle the selected material-group filter for the active service event."""
    state_key = f"material_group_selection_{selected_event}"
    current_value = st.session_state.get(state_key)
    st.session_state[state_key] = None if current_value == group_id else group_id


def _render_material_group_buttons(material_groups, selected_event):
    """Render the selectable material-group buttons for an event."""
    if not material_groups:
        st.info("No material groups linked to this service event.")
        return None

    group_count = len(material_groups)
    column_count = 1
    row_count = group_count
    container_height = max(220, 54 * group_count + 8 * max(group_count - 1, 0))
    button_gap = 8
    button_height = max(44, (container_height - button_gap * max(row_count - 1, 0)) / row_count)

    st.markdown(
        f"""
        <style>
        .material-group-box {{
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            height: auto;
            display: flex;
            flex-direction: column;
            gap: {button_gap}px;
        }}
        .material-group-box .stButton {{
            margin: 0;
            flex: 1 1 auto;
            height: {button_height}px;
        }}
        div[data-testid="stButton"] > button {{
            width: 100%;
            height: 100%;
            border: none;
            border-radius: 0 18px 18px 0;
            background: #ffffff;
            color: #0f172a;
            font-weight: 600;
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.4), 0 4px 10px rgba(15, 23, 42, 0.06);
            padding: 0.7rem 0.75rem 0.7rem 1.25rem;
            white-space: normal;
            line-height: 1.35;
            transition: all 0.18s ease-in-out;
            clip-path: polygon(12% 0%, 100% 0%, 100% 100%, 12% 100%, 0% 50%);
            transform: skewX(-8deg);
        }}
        div[data-testid="stButton"] > button > div {{
            transform: skewX(8deg);
        }}
        div[data-testid="stButton"] > button:hover {{
            background: #f8fafc;
            transform: skewX(-8deg) translateY(-1px);
            box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.5), 0 8px 18px rgba(15, 23, 42, 0.12);
        }}
        div[data-testid="stButton"] > button[kind="primary"] {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: #ffffff;
            box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.4), 0 8px 18px rgba(37, 99, 235, 0.25);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    state_key = f"material_group_selection_{selected_event}"
    selected_group = st.session_state.get(state_key)

    st.markdown("<div style='height:0.5in;'></div>", unsafe_allow_html=True)

    for group in material_groups:
        group_id = str(group.get("id", ""))
        group_desc = str(group.get("description", "")).strip()
        label = f"{group_id}\n{group_desc}" if group_desc else group_id
        is_selected = selected_group == group_id

        if st.button(
            label,
            key=f"{state_key}_{group_id}",
            type="primary" if is_selected else "secondary",
            width="stretch",
            on_click=_toggle_selected_group,
            args=(selected_event, group_id),
        ):
            pass

    return st.session_state.get(state_key)


def material_multiple_mgs_page():
    """Render the page for inspecting service events that have multiple material groups."""
    xlsx_path = os.path.join(config.locations.processed, config.processed_files.multiple_materialgroups+ "_processed.xlsx")
    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    valid_counts = _get_count_options(xlsx_path)
    if not valid_counts:
        st.info("No material-group sheets found in the workbook.")
        return

    title_col, selector_col = st.columns([0.72, 0.28])

    with title_col:
        st.subheader("Multiple Material Groups")
        st.write("Select the number of material groups linked to a service event and review the event details.")

    with selector_col:
        selected_count = st.selectbox(
            "",
            options=valid_counts,
            index=0,
            format_func=lambda value: f"{value} groups",
            label_visibility="collapsed",
        )

    events_by_count = _load_events_for_count(xlsx_path, selected_count)
    if not events_by_count:
        st.info(f"No event rows were found in the {selected_count}mgs sheet.")
        return

    event_names = [event["event"] for event in events_by_count]
    default_event = event_names[0]
    selected_event = st.session_state.get("selected_event", default_event)
    if selected_event not in event_names:
        selected_event = default_event

    left_col, middle_col, right_col = st.columns([0.22, 0.28, 0.50], vertical_alignment="top")

    list_table_height = 550
    heatmap_height = int(list_table_height * 0.90)

    with left_col:
        st.caption(f"{len(event_names)} events")
        with st.container(height=list_table_height):
            for event_item in events_by_count:
                event_name = event_item["event"]
                is_selected = st.session_state.get("selected_event") == event_name
                st.button(
                    f"{event_name}",
                    key=f"event_{selected_count}_{event_name}",
                    type="primary" if is_selected else "secondary",
                    width="stretch",
                    help="Select service event",
                    on_click=_set_selected_event,
                    args=(event_name,),
                )

    with middle_col:
        selected_event_data = next((item for item in events_by_count if item["event"] == selected_event), None)
        if selected_event_data is None:
            st.info("Select an event from the list to display its material group relationships.")
            return

        material_group_list = selected_event_data["material_groups"]
        _render_material_group_buttons(material_group_list, selected_event)

    with right_col:
        selected_event_data = next((item for item in events_by_count if item["event"] == selected_event), None)
        if selected_event_data is not None:
            st.markdown(
                f"<div style='text-align:center; font-weight:bold; font-size:18px; margin-top:0; margin-bottom:0.25rem;'>{selected_event}</div>",
                unsafe_allow_html=True,
            )
            table_df = _load_selected_event_data(xlsx_path, selected_count, selected_event)
            selected_material_group = st.session_state.get(f"material_group_selection_{selected_event}")
            if selected_material_group:
                table_df = table_df[table_df["Material Group ID"] == selected_material_group].reset_index(drop=True)
            if not table_df.empty:
                st.dataframe(
                    table_df.style.set_properties(**{"font-size": "11px"}),
                    width="stretch",
                    hide_index=True,
                    height=list_table_height,
                )
            else:
                st.info("No material rows for the selected material group. Showing all rows for this event by default.")


if __name__ == "__main__":
    material_multiple_mgs_page()