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


def build_material_tree(xlsx_path: Path, sheet_name: str):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    cols = list(df.columns)
    material_id_col = _find_col(cols, ["Itemnumber", "MaterialNumber", "Material", "Item Number"])
    material_name_col = _find_col(cols, ["MaterialName", "MaterialDescription", "Name", "Description"])
    event_col = _find_col(cols, ["Serviceeventcode", "Service Event Code"])
    and_or_col = _find_col(cols, ["AND_OR", "And_Or", "AND/OR"])

    if material_name_col is None and material_id_col is None:
        st.error("Could not find required material columns.")
        return []

    grouped = {}
    for _, row in df.iterrows():
        material_id = _normalize_name(row.get(material_id_col)) if material_id_col else ""
        material_name = _normalize_name(row.get(material_name_col)) if material_name_col else material_id
        event = _normalize_name(row.get(event_col)) if event_col else "Unknown"
        and_or = _normalize_name(row.get(and_or_col)) if and_or_col else ""

        if not material_name:
            continue

        record = grouped.setdefault(
            material_name,
            {"material_ids": set(), "events": {}},
        )

        if material_id:
            record["material_ids"].add(material_id)
        if event:
            record["events"].setdefault(event, set())
            if and_or:
                record["events"][event].add(and_or)

    result = []
    for key, value in grouped.items():
        events = {
            ev: sorted(and_ors) for ev, and_ors in value["events"].items()
        }
        result.append({
            "label": key,
            "material_ids": sorted(value["material_ids"]),
            "events": events,
        })
    return result


def _and_or_symbol(and_ors: list) -> str:
    """Map AND_OR values to a display symbol: & for AND, | for OR, - otherwise."""
    if not and_ors:
        return "-"
    joined = ",".join(and_ors).strip().upper()
    if "AND" in joined:
        return "&"
    if "OR" in joined:
        return "|"
    return "-"


def custom_event_badge_html(event_code: str, symbol: str, highlight: bool = False):
    if highlight:
        return f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            background: #1d4ed8;
            border-left: 8px solid #1e3a8a;
            border-radius: 14px;
            padding: 42px 34px;
            color: white;
            font-weight: 900;
            font-size: 1.6rem;
            box-shadow: 0 6px 14px rgba(29,78,216,0.35);
            min-height: 110px;
        ">
            <span>{event_code}</span>
            <span style="
                background: white;
                color: #1d4ed8;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 1.3rem;
            ">{symbol}</span>
        </div>
        """
    return f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        background: #dbeafe;
        border-left: 6px solid #3b82f6;
        border-radius: 10px;
        padding: 16px 20px;
        color: #0f172a;
        font-weight: 800;
        font-size: 1.15rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    ">
        <span>{event_code}</span>
        <span style="
            background: #3b82f6;
            color: white;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 1rem;
        ">{symbol}</span>
    </div>
    """


def _build_editor_df(nodes, selected_label=None):
    """Build a dataframe with View + Material columns, Move checkbox placed last."""
    rows = []
    for node in nodes:
        ids_str = " • ".join(node["material_ids"]) if node["material_ids"] else ""
        rows.append({
            "View": node["label"] == selected_label,
            "Material Name": node["label"],
            "Material IDs": ids_str,
            "Move": False,
        })
    return pd.DataFrame(rows)


def _render_event_badges(selected_node):
    """Render event badges one per line with generous spacing, highlighting the selected material's badges."""
    if selected_node is None:
        st.caption("Check the 'View' box on a material row to see related service events.")
        return

    st.markdown(f"**Service Events — {selected_node['label']}**")

    events = sorted(selected_node.get("events", {}).items())
    if not events:
        st.caption("No service events found for this material.")
        return

    badges_html = "".join(
        f'<div style="margin-bottom: 56px;">{custom_event_badge_html(ev, _and_or_symbol(and_ors), highlight=True)}</div>'
        for ev, and_ors in events
    )
    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column;">
            {badges_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_material_table(nodes):
    """Render exactly two tables: Main (left checkbox to view/move) and Corrected (below)."""
    if "moved_materials" not in st.session_state:
        st.session_state.moved_materials = set()
    if "main_selected_label" not in st.session_state:
        st.session_state.main_selected_label = None
    if "corrected_selected_label" not in st.session_state:
        st.session_state.corrected_selected_label = None

    moved = st.session_state.moved_materials
    main_nodes = [n for n in nodes if n["label"] not in moved]
    corrected_nodes = [n for n in nodes if n["label"] in moved]

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.markdown("**Materials**")
        main_df = _build_editor_df(main_nodes, st.session_state.main_selected_label)
        edited_main = st.data_editor(
            main_df,
            hide_index=True,
            use_container_width=True,
            height=560,
            column_order=["View", "Material Name", "Material IDs", "Move"],
            column_config={
                "View": st.column_config.CheckboxColumn("View"),
                "Material Name": st.column_config.TextColumn("Material Name", disabled=True),
                "Material IDs": st.column_config.TextColumn("Material IDs", disabled=True),
                "Move": st.column_config.CheckboxColumn("Prune"),
            },
            key="main_material_editor",
        )

        # Handle Move -> Corrected
        newly_moved = edited_main.loc[edited_main["Move"], "Material Name"].tolist()
        if newly_moved:
            st.session_state.moved_materials.update(newly_moved)
            if st.session_state.main_selected_label in newly_moved:
                st.session_state.main_selected_label = None
            st.rerun()

        # Handle View selection (single-select behavior)
        view_checked = edited_main.loc[edited_main["View"], "Material Name"].tolist()
        new_selection = next(
            (label for label in view_checked if label != st.session_state.main_selected_label),
            view_checked[0] if view_checked else None,
        )
        if new_selection != st.session_state.main_selected_label:
            st.session_state.main_selected_label = new_selection
            st.rerun()

    main_nodes_by_label = {n["label"]: n for n in main_nodes}
    selected_node = main_nodes_by_label.get(st.session_state.main_selected_label)

    with right_col:
        _render_event_badges(selected_node)

    st.markdown("---")
    st.markdown("**Corrected Materials**")
    if corrected_nodes:
        corrected_df = _build_editor_df(corrected_nodes, st.session_state.corrected_selected_label)
        # Rename Move column semantics for corrected table
        corrected_df = corrected_df.rename(columns={"Move": "Move Back"})

        edited_corrected = st.data_editor(
            corrected_df,
            hide_index=True,
            use_container_width=True,
            column_order=["View", "Material Name", "Material IDs", "Move Back"],
            column_config={
                "View": st.column_config.CheckboxColumn("View"),
                "Material Name": st.column_config.TextColumn("Material Name", disabled=True),
                "Material IDs": st.column_config.TextColumn("Material IDs", disabled=True),
                "Move Back": st.column_config.CheckboxColumn("Move Back"),
            },
            key="corrected_material_editor",
        )

        newly_back = edited_corrected.loc[edited_corrected["Move Back"], "Material Name"].tolist()
        if newly_back:
            st.session_state.moved_materials.difference_update(newly_back)
            if st.session_state.corrected_selected_label in newly_back:
                st.session_state.corrected_selected_label = None
            st.rerun()

        corrected_view_checked = edited_corrected.loc[edited_corrected["View"], "Material Name"].tolist()
        new_corrected_selection = next(
            (label for label in corrected_view_checked if label != st.session_state.corrected_selected_label),
            corrected_view_checked[0] if corrected_view_checked else None,
        )
        if new_corrected_selection != st.session_state.corrected_selected_label:
            st.session_state.corrected_selected_label = new_corrected_selection
            st.rerun()
    else:
        st.caption("No materials moved to Corrected yet.")


def material_duplicacy_page():
    st.subheader("Material Duplicity")
    st.write("Material appearing multiple times across different Service Events.")

    xlsx_path = os.path.join(config.locations.outputs, "service_event_analysis.xlsx")
    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    material_tree = build_material_tree(xlsx_path, sheet_name="material_duplicacy")
    if not material_tree:
        st.info("No material rows found.")
        return

    render_material_table(material_tree)


def main():
    material_duplicacy_page()


if __name__ == "__main__":
    main()


