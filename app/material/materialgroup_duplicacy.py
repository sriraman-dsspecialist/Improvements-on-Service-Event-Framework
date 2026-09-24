import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _normalize_name(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def _find_col(cols, candidates):
    for c in candidates:
        for col in cols:
            if str(col).strip().lower() == c.lower():
                return col
    return None


def _and_or_symbol(and_ors) -> str:
    """Map AND_OR value(s) to a display symbol: & for AND, | for OR, - otherwise."""
    if not and_ors:
        return "-"
    joined = ",".join(and_ors).strip().upper() if isinstance(and_ors, (set, list)) else str(and_ors).strip().upper()
    if "AND" in joined:
        return "&"
    if "OR" in joined:
        return "|"
    return "-"


def build_materialgroup_tree(xlsx_path: Path, sheet_name: str):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    cols = list(df.columns)
    group_col = _find_col(cols, ["MaterialGroup"])
    desc_col = _find_col(cols, ["MaterialGroupDescription"])
    event_col = _find_col(cols, ["Serviceeventcode"])
    and_or_col = _find_col(cols, ["AND_OR", "And_Or", "AND/OR"])

    if group_col is None or desc_col is None:
        st.error("Could not find required material group columns.")
        return []

    if event_col is None:
        rows = []
        for _, row in df.iterrows():
            group = _normalize_name(row.get(group_col))
            desc = _normalize_name(row.get(desc_col))
            rows.append({"group_id": group, "description": desc, "service_event": "Unknown"})
        df = pd.DataFrame(rows)

    grouped = {}
    for _, row in df.iterrows():
        group = _normalize_name(row.get(group_col))
        desc = _normalize_name(row.get(desc_col))
        event = _normalize_name(row.get(event_col)) if event_col else "Unknown"
        and_or = _normalize_name(row.get(and_or_col)) if and_or_col else ""

        if not group:
            continue

        key = f"{group} - {desc}" if desc else group
        grouped.setdefault(key, {"events": {}})
        if event:
            grouped[key]["events"].setdefault(event, set())
            if and_or:
                grouped[key]["events"][event].add(and_or)

    return [
        {"label": key, "events": {ev: sorted(and_ors) for ev, and_ors in sorted(v["events"].items())}}
        for key, v in grouped.items()
    ]


def custom_event_badge_html(event_code: str, symbol: str):
    return f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        background: #dbeafe;
        border-left: 6px solid #3b82f6;
        border-radius: 10px;
        padding: 9px 12px;
        color: #0f172a;
        font-weight: 800;
        font-size: 0.82rem;
        margin: 6px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        width: 100%;
        box-sizing: border-box;
    ">
        <span>{event_code}</span>
        <span style="
            background: #3b82f6;
            color: white;
            border-radius: 6px;
            padding: 3px 9px;
            font-size: 0.78rem;
        ">{symbol}</span>
    </div>
    """


def render_materialgroup_cards(nodes):
    for node in nodes:
        label = node["label"]
        events = node.get("events", {})

        with st.container(border=True):
            st.markdown(f"**{label}**")

            for ev, and_ors in events.items():
                st.markdown(custom_event_badge_html(ev, _and_or_symbol(and_ors)), unsafe_allow_html=True)


def materialgroup_duplicacy_page():
    st.subheader("Material Group Duplicity")
    st.write("Material Group appearing multiple times across different Service Events.")

    xlsx_path = os.path.join(config.locations.outputs, "service_event_analysis.xlsx")
    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    group_tree = build_materialgroup_tree(xlsx_path, sheet_name="materialGroup_duplicacy")
    if not group_tree:
        st.info("No material group rows found.")
        return

    chunk_size = 3
    columns = st.columns(chunk_size)

    for idx, col in enumerate(columns):
        with col:
            start = idx * ((len(group_tree) + chunk_size - 1) // chunk_size)
            end = start + ((len(group_tree) + chunk_size - 1) // chunk_size)
            render_materialgroup_cards(group_tree[start:end])


def main():
    materialgroup_duplicacy_page()


if __name__ == "__main__":
    main()


