import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _normalize_excel_column_name(column_name):
    """Normalize an Excel header by stripping spaces and underscores for matching."""
    return str(column_name).strip().lower().replace(" ", "").replace("_", "")


def _coerce_int(value):
    """Safely coerce a value to an integer or return None when conversion is not possible."""
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_event_material_group_summary(xlsx_path):
    """Load the event_materialGroup sheet and normalize the expected columns."""
    xlsx_path = Path(xlsx_path)
    sheet_name = "event_materialGroup"
    if not xlsx_path.exists():
        raise FileNotFoundError(f"File not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    if df.empty:
        return df

    event_col = None
    child_count_col = None

    normalized_map = {
        _normalize_excel_column_name(col): col for col in df.columns
    }

    for candidate in ["serviceeventcodeparent", "serviceeventcode", "serviceeventcode_parent"]:
        if candidate in normalized_map:
            event_col = normalized_map[candidate]
            break

    for candidate in ["childcount", "child_count", "countofchildmaterials", "count"]:
        if candidate in normalized_map:
            child_count_col = normalized_map[candidate]
            break

    if event_col is None or child_count_col is None:
        raise ValueError(
            f"Could not find required columns in sheet '{sheet_name}'. "
            f"Available columns: {list(df.columns)}"
        )

    summary = df[[event_col, child_count_col]].copy()
    summary = summary.rename(columns={event_col: "Serviceeventcode_parent", child_count_col: "child_count"})

    summary["Serviceeventcode_parent"] = summary["Serviceeventcode_parent"].astype(str).str.strip()
    summary["child_count"] = summary["child_count"].apply(_coerce_int)
    summary = summary.dropna(subset=["Serviceeventcode_parent", "child_count"]).reset_index(drop=True)
    summary = summary.sort_values(["child_count", "Serviceeventcode_parent"], ascending=[True, True]).reset_index(drop=True)
    return summary


def get_child_count_options(summary_df):
    """Return the unique child-count values from the parent summary data."""
    if summary_df is None or summary_df.empty:
        return []
    counts = sorted({int(row) for row in summary_df["child_count"].dropna().tolist() if _coerce_int(row) is not None})
    return counts


def get_serviceevent_options_for_child_count(summary_df, child_count):
    """Return the parent service event codes matching the selected child count."""
    if summary_df is None or summary_df.empty:
        return []

    normalized_child_count = _coerce_int(child_count)
    if normalized_child_count is None:
        return []

    filtered = summary_df[summary_df["child_count"] == normalized_child_count]
    return sorted(filtered["Serviceeventcode_parent"].dropna().astype(str).str.strip().unique().tolist())


def load_event_parent_child_rows(xlsx_path, service_event_code):
    """Load the event_parent_child sheet and filter by parent service event code."""
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.exists():
        raise FileNotFoundError(f"File not found: {xlsx_path}")

    df = pd.read_excel(xlsx_path, sheet_name="event_parent_child")
    if df.empty:
        return df

    normalized_map = {
        _normalize_excel_column_name(col): col for col in df.columns
    }

    event_col = None
    for candidate in ["serviceeventcodeparent", "serviceeventcode", "serviceeventcode_parent"]:
        if candidate in normalized_map:
            event_col = normalized_map[candidate]
            break

    if event_col is None:
        return df

    filtered = df[df[event_col].astype(str).str.strip().str.lower() == str(service_event_code).strip().lower()].copy()
    return filtered.reset_index(drop=True)


def _find_column_name(df, candidates):
    """Find the best matching column name from a set of normalized candidate aliases."""
    normalized_map = {_normalize_excel_column_name(col): col for col in df.columns}
    for candidate in candidates:
        if candidate in normalized_map:
            return normalized_map[candidate]
    return None


def _format_material_label(material_name, material_number):
    """Compose a readable material label using the material name and number if present."""
    name = "" if pd.isna(material_name) else str(material_name).strip()
    number = "" if pd.isna(material_number) else str(material_number).strip()

    if name and number:
        return f"{name} . {number}"
    if name:
        return name
    if number:
        return number
    return "Unknown material"


def _flatten_html(markup: str) -> str:
    """Strip indentation from generated HTML so it renders cleanly inside Streamlit."""
    return "\n".join(line.strip() for line in markup.strip().splitlines())


def custom_material_badge_html(label: str, bg_color: str = "#0ea5e9"):
    """Create the HTML badge used to show a material label in the disparity view."""
    markup = f"""
    <span style="
        display: flex;
        align-items: center;
        justify-content: center;
        height: 2.6em;
        min-height: 2.6em;
        max-height: 2.6em;
        line-height: 1.3;
        background: {bg_color};
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
        {label}
    </span>
    """
    return _flatten_html(markup)


def _materials_table_html(items: list) -> str:
    """Render a compact HTML table of child material entries for the selected parent."""
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


def _render_material_badges(detail_rows):
    """Render parent-child material cards grouped by child service event."""
    if detail_rows is None or detail_rows.empty:
        return

    child_event_col = _find_column_name(detail_rows, ["serviceeventcodechild", "serviceeventcode_child", "serviceeventcode"])
    parent_name_col = _find_column_name(detail_rows, ["materialnameparent", "materialname", "materialname_parent"])
    parent_number_col = _find_column_name(detail_rows, ["itemnumberparent", "itemnumber", "itemnumber_parent", "parent_material"])
    child_name_col = _find_column_name(detail_rows, ["materialnamechild", "materialname_child", "childmaterialname", "childmaterial_name"])
    child_number_col = _find_column_name(detail_rows, ["itemnumberchild", "itemnumber_child", "childmaterialnumber", "childmaterial_no", "child_material"])

    if not all([child_event_col, parent_name_col, parent_number_col, child_name_col, child_number_col]):
        st.warning("Material detail columns are missing from the workbook, so the badge view could not be rendered.")
        return

    badge_df = detail_rows[[child_event_col, parent_name_col, parent_number_col, child_name_col, child_number_col]].copy()
    badge_df.columns = ["child_event", "parent_name", "parent_number", "child_name", "child_number"]
    badge_df = badge_df.dropna(subset=["child_event", "parent_name", "parent_number", "child_name", "child_number"]).copy()
    badge_df["child_event"] = badge_df["child_event"].astype(str).str.strip()
    badge_df["parent_name"] = badge_df["parent_name"].astype(str).str.strip()
    badge_df["parent_number"] = badge_df["parent_number"].astype(str).str.strip()
    badge_df["child_name"] = badge_df["child_name"].astype(str).str.strip()
    badge_df["child_number"] = badge_df["child_number"].astype(str).str.strip()
    badge_df = badge_df[
        (badge_df["child_event"] != "")
        & (badge_df["parent_name"] != "")
        & (badge_df["parent_number"] != "")
        & (badge_df["child_name"] != "")
        & (badge_df["child_number"] != "")
    ].drop_duplicates().reset_index(drop=True)

    if badge_df.empty:
        st.info("No material details were found for the selected service event.")
        return

    grouped_cards = []
    for child_event, event_group in badge_df.groupby("child_event", sort=True):
        parent_rows_html = []
        for (parent_name, parent_number), parent_group in event_group.groupby(["parent_name", "parent_number"], sort=True):
            parent_label = _format_material_label(parent_name, parent_number)
            child_items = [
                _format_material_label(child_name, child_number)
                for child_name, child_number in parent_group[["child_name", "child_number"]].itertuples(index=False, name=None)
            ]
            child_list_html = "<br>".join(f"• {item}" for item in child_items)
            parent_rows_html.append(
                f"<tr><td style='padding:8px; text-align:left; font-weight:700; border-top:1px solid #e5e7eb;'>{parent_label}</td><td style='padding:8px; text-align:left; border-top:1px solid #e5e7eb;'>{child_list_html}</td></tr>"
            )
        grouped_cards.append((child_event, "".join(parent_rows_html)))

    columns = st.columns(2)
    for idx, (child_event, rows_html) in enumerate(grouped_cards):
        with columns[idx % 2]:
            st.markdown(custom_material_badge_html(child_event, bg_color="#0ea5e9"), unsafe_allow_html=True)
            if rows_html:
                st.markdown(
                    f"""
                    <table style="width:100%; border-collapse: collapse; table-layout: fixed; font-size:0.85rem; color:#1f2937;">
                        <tbody>
                            {rows_html}
                        </tbody>
                    </table>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("No parent materials", unsafe_allow_html=False)


def disparity_parent_child_page():
    """Render the parent-child material disparity dashboard."""
    st.title("Disparity observed between parent and child materials")
    st.write("Parent material belonging to a particular service event and its associated child materials may be spread out in different service events")
    xlsx_path = os.path.join(config.locations.processed, config.processed_files.disparity_materials+ "_processed.xlsx")

    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    try:
        summary = load_event_material_group_summary(xlsx_path)
    except Exception as exc:  # pragma: no cover - UI path only
        st.error(f"Unable to read the summary sheet: {exc}")
        return

    if summary.empty:
        st.info("No event/material-group data was found in the summary sheet.")
        return

    child_count_options = get_child_count_options(summary)
    if not child_count_options:
        st.info("No child counts were found in the summary sheet.")
        return

    selected_child_count = st.select_slider(
        "Child count",
        options=child_count_options,
        value=child_count_options[0],
        help="Choose the number of child materials associated with a parent service event.",
    )

    service_event_options = get_serviceevent_options_for_child_count(summary, selected_child_count)
    if not service_event_options:
        st.info(f"No service event codes are available for child count {selected_child_count}.")
        return

    selected_service_event = st.selectbox(
        "Service event code",
        options=service_event_options,
        help="This list is filtered to the selected child count.",
    )

    detail_rows = load_event_parent_child_rows(xlsx_path, selected_service_event)
    st.subheader(f"Materials for {selected_service_event}")
    if detail_rows.empty:
        st.info("No matching parent/child records were found for the selected service event code.")
        return

    _render_material_badges(detail_rows)


def main():
    """Entry point for the parent-child disparity dashboard."""
    disparity_parent_child_page()


if __name__ == "__main__":
    main()

