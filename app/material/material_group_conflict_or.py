import html
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


def _and_or_symbol(value: str) -> str:
    """Map an AND_OR value to a display symbol: & for AND, | for OR, - otherwise."""
    joined = (value or "").strip().upper()
    if "AND" in joined:
        return "&"
    if "OR" in joined:
        return "|"
    return "-"


def load_material_group_conflicts(xlsx_path: str):
    df = pd.read_excel(xlsx_path, sheet_name="material_vs_materialGroup")

    cols = list(df.columns)
    event_primary_col = _find_col(cols, ["Serviceeventcode_primary"])
    material_col = _find_col(cols, ["Itemnumber"])
    material_name_col = _find_col(cols, ["MaterialName"])
    material_group_col = _find_col(cols, ["MaterialGroup"])
    material_group_desc_col = _find_col(cols, ["MaterialGroupDescription"])
    event_secondary_col = _find_col(cols, ["Serviceeventcode_secondary"])
    and_or_primary_col = _find_col(cols, ["AND_OR_primary"])
    and_or_secondary_col = _find_col(cols, ["AND_OR_secondary"])

    required_cols = {
        "Serviceeventcode_primary": event_primary_col,
        "Itemnumber": material_col,
        "MaterialName": material_name_col,
        "MaterialGroup": material_group_col,
        "MaterialGroupDescription": material_group_desc_col,
        "Serviceeventcode_secondary": event_secondary_col,
        "AND_OR_primary": and_or_primary_col,
    }
    missing = [name for name, col in required_cols.items() if col is None]
    if missing:
        st.error(f"Missing columns in sheet 'material_vs_materialGroup': {missing}")
        st.write("Available columns:", cols)
        return pd.DataFrame(columns=list(required_cols.keys()))

    df = df.loc[df[and_or_primary_col] != "AND"]
    df = df.head(100)

    rows = []
    for _, row in df.iterrows():
        primary_event = _normalize_name(row[event_primary_col])
        material = _normalize_name(row[material_col])
        material_name = _normalize_name(row[material_name_col])
        material_group = _normalize_name(row[material_group_col])
        material_group_desc = _normalize_name(row[material_group_desc_col])
        secondary_event = _normalize_name(row[event_secondary_col])
        and_or_primary = _normalize_name(row[and_or_primary_col])
        and_or_secondary = _normalize_name(row[and_or_secondary_col]) if and_or_secondary_col else ""

        if not material or not material_group:
            continue

        if primary_event and secondary_event and primary_event == secondary_event:
            continue

        rows.append({
            "Serviceeventcode_primary": primary_event,
            "and_or_primary": and_or_primary,
            "material": material,
            "materialname": material_name,
            "materialgroup": material_group,
            "materialgroupdescription": material_group_desc,
            "Serviceeventcode_secondary": secondary_event,
            "and_or_secondary": and_or_secondary,
        })

    return pd.DataFrame(rows, columns=[
        "Serviceeventcode_primary",
        "and_or_primary",
        "material",
        "materialname",
        "materialgroup",
        "materialgroupdescription",
        "Serviceeventcode_secondary",
        "and_or_secondary",
    ])


def _large_badge_html(event_code: str, symbol: str, bg_color: str, border_color: str) -> str:
    """Render a large event badge with its AND_OR symbol."""
    if not event_code:
        event_code = "No event"
        bg_color = "#f3f4f6"
        border_color = "#9ca3af"

    return f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 14px;
        min-height: 180px;
        background: {bg_color};
        border-left: 8px solid {border_color};
        border-radius: 12px;
        padding: 26px 20px;
        color: #111827;
        font-weight: 800;
        font-size: 0.95rem;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.10);
        word-break: break-word;
        text-align: center;
    ">
        <span>{event_code}</span>
        <span style="
            background: {border_color};
            color: white;
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 0.9rem;
        ">{symbol}</span>
    </div>
    """


def _group_by_material_name(df: pd.DataFrame) -> pd.DataFrame:
    """Combine rows sharing the same material name, collecting all their material IDs and
    material groups together, then sort the result by material name."""
    grouped = {}
    order = []
    for _, row in df.iterrows():
        key = row["materialname"]
        if key not in grouped:
            grouped[key] = {
                "material_ids": set(),
                "materialgroups": set(),
                "materialgroupdescription": row["materialgroupdescription"],
                "Serviceeventcode_primary": row["Serviceeventcode_primary"],
                "and_or_primary": row["and_or_primary"],
                "Serviceeventcode_secondary": row["Serviceeventcode_secondary"],
                "and_or_secondary": row["and_or_secondary"],
            }
            order.append(key)
        grouped[key]["material_ids"].add(row["material"])
        grouped[key]["materialgroups"].add(row["materialgroup"])

    rows = []
    for materialname in order:
        entry = grouped[materialname]
        rows.append({
            "material": sorted(entry["material_ids"]),
            "materialname": materialname,
            "materialgroup": sorted(entry["materialgroups"]),
            "materialgroupdescription": entry["materialgroupdescription"],
            "Serviceeventcode_primary": entry["Serviceeventcode_primary"],
            "and_or_primary": entry["and_or_primary"],
            "Serviceeventcode_secondary": entry["Serviceeventcode_secondary"],
            "and_or_secondary": entry["and_or_secondary"],
        })

    result = pd.DataFrame(rows)
    return result.sort_values(by="materialname", key=lambda s: s.str.lower()).reset_index(drop=True)


def _cell_html(lines, total_lines: int, bold: bool = False) -> str:
    """Render a cell as centered, multi-line HTML (one item per line via <br>), vertically
    centered against the tallest cell in the same row."""
    if isinstance(lines, list):
        items = [html.escape(str(v)) for v in lines]
    else:
        items = [html.escape(str(lines))] if lines else [""]
    content = "<br>".join(items) if items else "&nbsp;"

    line_height = 22
    min_height = max(total_lines, 1) * line_height
    weight = "700" if bold else "500"

    return f"""
    <div style="
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: {min_height}px;
        text-align: center;
        font-size: 0.85rem;
        font-weight: {weight};
        line-height: 1.4;
        padding: 4px 6px;
    ">{content}</div>
    """


def _header_cell_html(label: str) -> str:
    """Render a bold, larger table header cell that can wrap onto two lines."""
    return f"""
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 1.05rem;
        font-weight: 800;
        line-height: 1.25;
        min-height: 2.6em;
        padding: 6px 6px;
    ">{html.escape(label)}</div>
    """


def _row_divider_html(thick: bool = False) -> str:
    """A single full-width horizontal rule spanning the whole row, used instead of per-cell borders
    so the line stays straight even when cells have different rendered heights."""
    border = "2px solid #374151" if thick else "1px solid #d1d5db"
    return f"<hr style='margin: 0; border: none; border-top: {border};'>"


def _on_view_toggle(row_key: str, idx):
    """Enforce single-select behavior across the View checkboxes."""
    if st.session_state.get(row_key):
        st.session_state.conflict_selected_idx = idx
        for key in list(st.session_state.keys()):
            if key.startswith("conflict_view_") and key != row_key:
                st.session_state[key] = False
    elif st.session_state.conflict_selected_idx == idx:
        st.session_state.conflict_selected_idx = None


def _combo_title(name: str, ids: list) -> str:
    """Build a 'Name - ID1 • ID2' style title for a badge."""
    ids_str = " • ".join(ids) if ids else ""
    return f"{name} - {ids_str}" if ids_str else name


def render_conflict_table(df: pd.DataFrame):
    """Render a 15-row table on the left, with the two event badges stacked on the right."""
    if "conflict_selected_idx" not in st.session_state:
        st.session_state.conflict_selected_idx = None

    table_col, badge_col = st.columns([3, 1])

    with table_col:
        header_cols = st.columns([2, 3, 1, 2, 3])
        for header_col, label in zip(
            header_cols, ["Material ID", "Material Name", "View", "Material Group", "Material Group Name"]
        ):
            header_col.markdown(_header_cell_html(label), unsafe_allow_html=True)
        st.markdown(_row_divider_html(thick=True), unsafe_allow_html=True)

        with st.container(height=560):
            for idx, row in df.iterrows():
                material_lines = row["material"]
                group_lines = row["materialgroup"]
                total_lines = max(len(material_lines), len(group_lines))

                row_key = f"conflict_view_{idx}"
                if row_key not in st.session_state:
                    st.session_state[row_key] = idx == st.session_state.conflict_selected_idx

                row_cols = st.columns([2, 3, 1, 2, 3])
                row_cols[0].markdown(_cell_html(material_lines, total_lines), unsafe_allow_html=True)
                row_cols[1].markdown(_cell_html(row["materialname"], total_lines, bold=True), unsafe_allow_html=True)
                with row_cols[2]:
                    st.markdown(
                        "<div style='height: 100%; display:flex; align-items:center; justify-content:center;'>",
                        unsafe_allow_html=True,
                    )
                    st.checkbox(
                        "",
                        key=row_key,
                        on_change=_on_view_toggle,
                        args=(row_key, idx),
                        label_visibility="collapsed",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                row_cols[3].markdown(_cell_html(group_lines, total_lines), unsafe_allow_html=True)
                row_cols[4].markdown(
                    _cell_html(row["materialgroupdescription"], total_lines, bold=True),
                    unsafe_allow_html=True,
                )
                st.markdown(_row_divider_html(), unsafe_allow_html=True)

    selected_idx = st.session_state.conflict_selected_idx
    if selected_idx is not None and selected_idx not in df.index:
        selected_idx = None
        st.session_state.conflict_selected_idx = None
    selected_row = df.loc[selected_idx] if selected_idx is not None else None

    with badge_col:
        if selected_row is not None:
            material_title = _combo_title(selected_row["materialname"], selected_row["material"])
            group_title = _combo_title(selected_row["materialgroupdescription"], selected_row["materialgroup"])

            st.markdown(f"**{material_title}**")
            symbol = _and_or_symbol(selected_row["and_or_primary"])
            st.markdown(
                _large_badge_html(selected_row["Serviceeventcode_primary"], symbol, "#eefaf0", "#22c55e"),
                unsafe_allow_html=True,
            )

            st.markdown(f"**{group_title}**")
            symbol = _and_or_symbol(selected_row["and_or_secondary"])
            st.markdown(
                _large_badge_html(selected_row["Serviceeventcode_secondary"], symbol, "#fff7ed", "#f59e0b"),
                unsafe_allow_html=True,
            )
        else:
            st.caption("Check 'View' on a row to see the events.")


def material_group_conflict_page_or():
    st.subheader("Material vs Material Group Service Event Conflict")

    xlsx_path = os.path.join(config.locations.outputs, "service_event_analysis.xlsx")

    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    df = load_material_group_conflicts(xlsx_path)

    if df.empty:
        st.info("No conflicting rows found in the sheet 'material_vs_materialGroup'.")
        return

    grouped_df = _group_by_material_name(df)
    render_conflict_table(grouped_df)


def main():
    material_group_conflict_page_or()


if __name__ == "__main__":
    main()

