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


def load_material_group_conflicts(xlsx_path: str):
    df = pd.read_excel(xlsx_path, sheet_name="material_vs_materialGroup")
    df = df.head(100)

    required = [
        "Serviceeventcode_primary",
        "Itemnumber",
        "MaterialName",
        "MaterialGroup",
        "MaterialGroupDescription",
        "Serviceeventcode_secondary",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"Missing columns in sheet 'material_vs_materialGroup': {missing}")
        st.write("Available columns:", list(df.columns))
        return pd.DataFrame(columns=required)

    rows = []
    for _, row in df.iterrows():
        primary_event = _normalize_name(row["Serviceeventcode_primary"])
        material = _normalize_name(row["Itemnumber"])
        material_name = _normalize_name(row["MaterialName"])
        material_group = _normalize_name(row["MaterialGroup"])
        material_group_desc = _normalize_name(row["MaterialGroupDescription"])
        secondary_event = _normalize_name(row["Serviceeventcode_secondary"])

        if not material or not material_group:
            continue

        if primary_event and secondary_event and primary_event == secondary_event:
            continue

        rows.append({
            "Serviceeventcode_primary": primary_event,
            "material": material,
            "materialname": material_name,
            "materialgroup": material_group,
            "materialgroupdescription": material_group_desc,
            "Serviceeventcode_secondary": secondary_event,
        })

    return pd.DataFrame(rows, columns=[
        "Serviceeventcode_primary",
        "material",
        "materialname",
        "materialgroup",
        "materialgroupdescription",
        "Serviceeventcode_secondary",
    ])


def event_badge(event_code: str, bg_color: str, border_color: str):
    if not event_code:
        event_code = "No event"
        bg_color = "#f3f4f6"
        border_color = "#9ca3af"

    st.markdown(
        f"""
        <span style="
            display: inline-block;
            background: {bg_color};
            border-left: 5px solid {border_color};
            border-radius: 8px;
            padding: 9px 12px;
            color: #111827;
            font-weight: 700;
            text-align: center;
            min-width: 120px;
            min-height: 42px;
            line-height: 1.2;
        ">
            {event_code}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_conflict_card(row):
    material_label = f"{row['material']} — {row['materialname']}" if row["materialname"] else row["material"]
    group_label = f"{row['materialgroup']} — {row['materialgroupdescription']}" if row["materialgroupdescription"] else row["materialgroup"]

    with st.container():
        st.markdown(
            f"""
            <div style="
                border: 1px solid #d1d5db;
                border-radius: 12px;
                background: #ffffff;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
                padding: 14px;
                margin-bottom: 18px;
                min-height: 120px;
            ">
                <div style="font-size: 1.0rem; font-weight: 700; margin-bottom: 6px; line-height: 1.3;">
                    {material_label}
                </div>
                <div style="color: #4b5563; margin-bottom: 10px; font-size: 0.9rem; line-height: 1.3;">
                    {group_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left_col, right_col = st.columns(2)
        with left_col:
            event_badge(row["Serviceeventcode_primary"], "#eefaf0", "#22c55e")
        with right_col:
            event_badge(row["Serviceeventcode_secondary"], "#fff7ed", "#f59e0b")


def material_group_conflict_page():
    st.subheader("Material vs Material Group Service Event Conflict")

    xlsx_path = os.path.join(config.locations.outputs, "service_event_analysis.xlsx")

    if not os.path.exists(xlsx_path):
        st.warning(f"File not found: {xlsx_path}")
        return

    df = load_material_group_conflicts(xlsx_path)

    if df.empty:
        st.info("No conflicting rows found in the sheet 'material_vs_materialGroup'.")
        return

    chunk_size = 3
    columns = st.columns(chunk_size)

    for idx, col in enumerate(columns):
        with col:
            start = idx * ((len(df) + chunk_size - 1) // chunk_size)
            end = start + ((len(df) + chunk_size - 1) // chunk_size)
            for _, row in df.iloc[start:end].iterrows():
                render_conflict_card(row)


def main():
    material_group_conflict_page()


if __name__ == "__main__":
    main()


