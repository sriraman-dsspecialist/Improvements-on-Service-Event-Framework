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


def _flatten_html(markup: str) -> str:
    """Strip leading whitespace per line so Markdown doesn't treat indented HTML as a code block."""
    return "\n".join(line.strip() for line in markup.strip().splitlines())


def build_materialgroup_tree(xlsx_path: Path, sheet_name: str):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    cols = list(df.columns)
    group_col = _find_col(cols, ["MaterialGroup"])
    desc_col = _find_col(cols, ["MaterialGroupDescription"])
    event_col = _find_col(cols, ["Serviceeventcode"])
    material_name_col = _find_col(cols, ["MaterialName"])
    material_id_col = _find_col(cols, ["Itemnumber"])

    if group_col is None or desc_col is None:
        st.error("Could not find required material group columns.")
        return []

    grouped = {}
    for _, row in df.iterrows():
        group = _normalize_name(row.get(group_col))
        desc = _normalize_name(row.get(desc_col))
        event = _normalize_name(row.get(event_col)) if event_col else "Unknown"
        material_name = _normalize_name(row.get(material_name_col)) if material_name_col else ""
        material_id = _normalize_name(row.get(material_id_col)) if material_id_col else ""

        if not group:
            continue

        grouped.setdefault(group, {"description": desc, "events": {}})
        if event:
            grouped[group]["events"].setdefault(event, set())
            if material_name or material_id:
                grouped[group]["events"][event].add((material_name, material_id))

    result = []
    for group, data in grouped.items():
        events = data["events"]
        event_names = list(events.keys())

        # Find (name, id) pairs common across all events for this group and remove them
        if len(event_names) >= 2:
            common = set.intersection(*[events[e] for e in event_names]) if events else set()
        else:
            common = set()

        cleaned_events = {
            e: sorted(pairs - common, key=lambda p: (p[0], p[1]))
            for e, pairs in events.items()
        }

        result.append({
            "group_id": group,
            "description": data["description"],
            "events": cleaned_events,
        })

    return result


def _format_materials(pairs):
    """Group (name, id) pairs by material name and merge ids with bold dot separator."""
    grouped = {}
    for name, mid in pairs:
        grouped.setdefault(name, [])
        if mid:
            grouped[name].append(mid)

    formatted = []
    for name in sorted(grouped.keys()):
        ids = sorted(set(grouped[name]))
        if ids:
            formatted.append(f"{name} - {' • '.join(ids)}")
        else:
            formatted.append(name)
    return formatted


def custom_event_badge_html(event_code: str):
    markup = f"""
    <span style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2.6em;
        min-height: 2.6em;
        max-height: 2.6em;
        line-height: 1.3;
        background: #d451db;
        color: white;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 6px 10px;
        border-radius: 6px 6px 0 0;
        text-align: center;
        word-break: break-word;
        box-sizing: border-box;
        overflow: hidden;
    ">
        {event_code}
    </span>
    """
    return _flatten_html(markup)


def _materials_table_html(items: list) -> str:
    """Render materials as a header-less table with horizontal borders only."""
    rows_html = "".join(
        f"""
        <tr>
            <td style="
                border-top: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                padding: 8px;
                text-align: center;
                font-size: 0.85rem;
                white-space: normal;
                word-wrap: break-word;
                overflow-wrap: break-word;
                word-break: break-word;
            ">{item}</td>
        </tr>
        """
        for item in items
    )
    markup = f"""
    <table style="width: 100%; border-collapse: collapse; table-layout: fixed;">
        {rows_html}
    </table>
    """
    return _flatten_html(markup)


def render_event_material_table(event_name: str, materials: list):
    st.markdown(custom_event_badge_html(event_name), unsafe_allow_html=True)
    formatted_materials = _format_materials(materials)
    if formatted_materials:
        st.markdown(_materials_table_html(formatted_materials), unsafe_allow_html=True)
    else:
        st.markdown(
            _flatten_html(
                """
                <div style="
                    border: 1px solid #e5e7eb;
                    border-top: none;
                    padding: 8px;
                    font-size: 0.8rem;
                    color: #6b7280;
                    text-align: center;
                ">
                    No unique materials
                </div>
                """
            ),
            unsafe_allow_html=True,
        )


def render_materialgroup_cards(nodes):
    for node in nodes:
        group_id = node["group_id"]
        description = node["description"]
        events = node.get("events", {})
        event_names = list(events.keys())

        with st.container(border=True):
            title = f"{group_id} - {description}" if description else group_id
            st.markdown(f"**{title}**")

            if not event_names:
                st.info("No service events found for this group.")
                continue

            # Show up to two events side by side as separate tables
            table_cols = st.columns(min(len(event_names), 2) or 1)
            for idx, event_name in enumerate(event_names[:2]):
                with table_cols[idx % len(table_cols)]:
                    render_event_material_table(event_name, events[event_name])

            # If more than 2 events exist, render remaining ones below
            for event_name in event_names[2:]:
                render_event_material_table(event_name, events[event_name])


def _node_weight(node) -> int:
    """Estimate a card's rendered height so columns can be balanced by content, not just count."""
    events = node.get("events", {})
    weight = 2  # card title + padding
    for materials in events.values():
        weight += 2 + max(len(materials), 1)  # badge + table rows for this event
    return weight


def split_nodes_into_columns(nodes, chunk_size):
    """Distribute nodes across columns balancing total estimated content weight, not raw count,
    so no column ends up mostly empty while another is overloaded."""
    if not nodes:
        return [[] for _ in range(chunk_size)]

    columns = [[] for _ in range(chunk_size)]
    column_weights = [0] * chunk_size

    for node in sorted(nodes, key=_node_weight, reverse=True):
        target = column_weights.index(min(column_weights))
        columns[target].append(node)
        column_weights[target] += _node_weight(node)

    return columns


def materialgroup_mixie_page():
    st.subheader("Material Group Mixie")
    st.write("Materials belonging to a given Material Group belonging to different Service Events")

    xlsx_path = os.path.join(config.locations.outputs, "service_event_analysis.xlsx")
    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    group_tree = build_materialgroup_tree(xlsx_path, sheet_name="materialgroup_nEvents_list")
    if not group_tree:
        st.info("No material group rows found.")
        return

    chunk_size = 2
    columns = st.columns(chunk_size)
    split_groups = split_nodes_into_columns(group_tree, chunk_size)

    for col, nodes in zip(columns, split_groups):
        with col:
            render_materialgroup_cards(nodes)


def main():
    materialgroup_mixie_page()


if __name__ == "__main__":
    main()


