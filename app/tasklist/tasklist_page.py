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


def build_tasklist_tree(xlsx_path: Path):
    df = pd.read_excel(xlsx_path)

    cols = list(df.columns)
    task_col = _find_col(cols, ["TaskListGroup"])
    desc_col = _find_col(cols, ["TaskListDescription"])
    event_col = _find_col(cols, ["Serviceeventcode"])

    if task_col is None or desc_col is None:
        st.error("Could not find the required tasklist columns in the Excel file.")
        return []

    if event_col is None:
        rows = []
        for _, row in df.iterrows():
            task_id = _normalize_name(row.get(task_col))
            desc = _normalize_name(row.get(desc_col))
            rows.append({
                "tasklist_id": task_id,
                "description": desc,
                "service_event": "Unknown service event"
            })
        df = pd.DataFrame(rows)

    grouped = {}
    for _, row in df.iterrows():
        task_id = _normalize_name(row.get(task_col))
        desc = _normalize_name(row.get(desc_col))
        event = _normalize_name(row.get(event_col)) if event_col else "Unknown service event"

        if not task_id:
            continue

        key = f"{task_id} - {desc}" if desc else task_id
        grouped.setdefault(key, {"events": set()})
        if event:
            grouped[key]["events"].add(event)

    return [{"label": key, "events": sorted(v["events"])} for key, v in grouped.items()]


def custom_event_badge_html(event_code: str, bg_color: str = "#fef3c7", border_color: str = "#f59e0b"):
    return f"""
    <span style="
        display: block;
        background: {bg_color};
        border-left: 5px solid {border_color};
        border-radius: 8px;
        padding: 9px 12px;
        color: #0f172a;
        font-weight: 800;
        font-size: 0.82rem;
        margin: 6px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        width: 100%;
    ">
        {event_code}
    </span>
    """


def render_tasklist_cards(nodes):
    for node in nodes:
        label = node["label"]
        events = node.get("events", [])

        with st.container(border=True):
            st.markdown(f"**{label}**")

            if events:
                for ev in events:
                    st.markdown(custom_event_badge_html(ev, bg_color="#fef3c7", border_color="#f59e0b"), unsafe_allow_html=True)


def page1():
    st.subheader("Task List Duplicity")
    st.write("TaskListGroups appearing multiple times across different Service Events.")

    xlsx_path = os.path.join(config.locations.outputs, "tasklistgroup_analysis.xlsx")
    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    tasklist_tree = build_tasklist_tree(xlsx_path)
    if not tasklist_tree:
        st.info("No tasklist rows found.")
        return

    chunk_size = 3
    columns = st.columns(chunk_size)

    for idx, col in enumerate(columns):
        with col:
            start = idx * ((len(tasklist_tree) + chunk_size - 1) // chunk_size)
            end = start + ((len(tasklist_tree) + chunk_size - 1) // chunk_size)
            render_tasklist_cards(tasklist_tree[start:end])


def main():
    page1()


if __name__ == "__main__":
    main()