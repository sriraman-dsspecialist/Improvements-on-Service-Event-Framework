import json
import os
import sys
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _normalize_event_name(value):
    """Normalize event names by trimming whitespace and converting to lowercase."""
    return " ".join(str(value).strip().split()).casefold()


def _pair_key(event1, event2):
    """Create a stable key for an unordered pair of event names."""
    return tuple(sorted([_normalize_event_name(event1), _normalize_event_name(event2)]))


def _canonicalize_pair_table(df):
    """Sort and deduplicate event pairs into a standard pair layout for output."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Primary Event", "Secondary Event"])

    normalized = df[["Primary Event", "Secondary Event"]].copy()
    normalized["Primary Event"] = normalized["Primary Event"].astype(str).map(lambda x: " ".join(x.strip().split()))
    normalized["Secondary Event"] = normalized["Secondary Event"].astype(str).map(lambda x: " ".join(x.strip().split()))
    normalized["pair_key"] = normalized.apply(
        lambda row: _pair_key(row["Primary Event"], row["Secondary Event"]),
        axis=1,
    )
    normalized = normalized.drop_duplicates(subset=["pair_key"], keep="first").copy()
    normalized["ordered_pair"] = normalized.apply(
        lambda row: tuple(sorted([row["Primary Event"], row["Secondary Event"]], key=lambda x: _normalize_event_name(x))),
        axis=1,
    )
    normalized[["Primary Event", "Secondary Event"]] = normalized["ordered_pair"].apply(
        lambda pair: pd.Series(pair, index=["Primary Event", "Secondary Event"])
    )
    return normalized[["Primary Event", "Secondary Event"]].reset_index(drop=True)


def _show_tooltip_message(message, duration_ms=10000):
    """Display a temporary toast-style tooltip message in the Streamlit app."""
    safe_message = json.dumps(message)
    st.components.v1.html(
        f"""
        <script>
        const toast = document.createElement('div');
        toast.setAttribute('data-testid', 'event-cluster-tooltip');
        toast.style.position = 'fixed';
        toast.style.right = '20px';
        toast.style.bottom = '20px';
        toast.style.zIndex = '999999';
        toast.style.background = 'rgba(17, 24, 39, 0.92)';
        toast.style.color = '#f8fafc';
        toast.style.padding = '10px 16px';
        toast.style.borderRadius = '10px';
        toast.style.boxShadow = '0 8px 24px rgba(15, 23, 42, 0.22)';
        toast.style.fontSize = '14px';
        toast.style.fontWeight = '600';
        toast.style.lineHeight = '1.4';
        toast.style.pointerEvents = 'none';
        toast.textContent = {safe_message};
        document.body.appendChild(toast);
        setTimeout(function() {{
            if (toast && toast.parentNode) {{
                toast.parentNode.removeChild(toast);
            }}
        }}, {duration_ms});
        </script>
        """,
        height=0,
    )


def _load_event_pairs():
    """Load the processed event-pair similarity data from the saved workbook."""
    workbook_path = os.path.join(config.locations.processed, config.processed_files.event_inconsistencies+ "_processed.xlsx")

    if not os.path.exists(workbook_path):
        st.error(f"Workbook not found: {workbook_path}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(workbook_path, sheet_name="Event Clustering")
    except ValueError:
        st.error("The workbook does not contain the 'Event Clustering' sheet.")
        return pd.DataFrame()

    required_cols = {"event1", "event2", "similarity"}
    missing_cols = required_cols.difference(df.columns)
    if missing_cols:
        st.error(f"The 'Event Clustering' sheet is missing required columns: {sorted(missing_cols)}")
        return pd.DataFrame()

    cluster_df = df[["event1", "event2", "similarity"]].copy()
    cluster_df["similarity"] = pd.to_numeric(cluster_df["similarity"], errors="coerce")
    cluster_df = cluster_df.dropna(subset=["similarity"]).copy()

    cluster_df["event1"] = cluster_df["event1"].astype(str).map(lambda x: " ".join(x.strip().split()))
    cluster_df["event2"] = cluster_df["event2"].astype(str).map(lambda x: " ".join(x.strip().split()))

    cluster_df["pair_key"] = cluster_df.apply(
        lambda row: _pair_key(row["event1"], row["event2"]),
        axis=1,
    )

    cluster_df = cluster_df.sort_values("similarity", ascending=False)
    cluster_df = cluster_df.drop_duplicates(subset=["pair_key"], keep="first").copy()

    cluster_df["ordered_pair"] = cluster_df.apply(
        lambda row: tuple(sorted([row["event1"], row["event2"]], key=lambda x: _normalize_event_name(x))),
        axis=1,
    )
    cluster_df[["event1", "event2"]] = cluster_df["ordered_pair"].apply(
        lambda pair: pd.Series(pair, index=["event1", "event2"])
    )

    cluster_df = cluster_df[["event1", "event2", "similarity"]]
    cluster_df["similarity"] = cluster_df["similarity"].apply(
        lambda value: round(value, 2) if pd.notna(value) and value < 0.8 else round(value, 1)
    )
    return cluster_df.reset_index(drop=True)


def event_clusters():
    """Render the service event clustering dashboard with similarity threshold controls."""
    st.title("Event Clustering")
    st.write("Service Events are clustered on similarities based on their names.")
    st.markdown(
        """
        <style>
        div[role="radiogroup"] {
            width: 100% !important;
            display: flex !important;
            gap: 0.45rem !important;
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            align-items: stretch !important;
            white-space: nowrap !important;
            padding-bottom: 0.15rem !important;
        }
        div[role="radiogroup"] > div {
            flex: 1 1 6.2rem !important;
            min-width: 6.2rem !important;
            max-width: 7rem !important;
        }
        div[role="radiogroup"] [role="radio"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
            min-height: 3.2rem !important;
            min-width: 6.2rem !important;
            font-size: 1.08rem !important;
            font-weight: 600 !important;
            padding: 0.8rem 1.2rem !important;
            border-radius: 12px !important;
            border: 1px solid rgba(148, 163, 184, 0.35) !important;
            background: rgba(255,255,255,0.04) !important;
            color: #e2e8f0 !important;
            transition: all 0.15s ease-in-out !important;
            white-space: nowrap !important;
        }
        div[role="radiogroup"] [role="radio"][aria-checked="true"] {
            background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
            border-color: #93c5fd !important;
            color: white !important;
            box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.55) !important;
            transform: none !important;
        }
        div[data-testid="stButton"] button {
            background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
            color: white !important;
            border: none !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
        }
        div[data-testid="stDataFrameWrapper"] td {
            font-size: 1.08rem !important;
        }
        div[data-testid="stDataFrameWrapper"] th {
            font-size: 1.12rem !important;
        }
        div[data-testid="stDataFrameWrapper"] [data-column="0"],
        div[data-testid="stDataFrameWrapper"] th:first-child,
        div[data-testid="stDataFrameWrapper"] td:first-child {
            width: 52px !important;
            min-width: 52px !important;
            max-width: 52px !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cluster_df = _load_event_pairs()
    if cluster_df.empty:
        return

    thresholds = [0.6, 0.65, 0.7, 0.75, 0.8, 0.9]
    selected_raw = st.pills(
        "",
        options=thresholds,
        selection_mode="single",
        default=0.8,
        format_func=lambda value: f"{value:g}",
        key="event_cluster_threshold",
    )
    selected_threshold = float(selected_raw) if selected_raw is not None else 0.8

    def is_in_threshold(score):
        if selected_threshold == 0.6:
            return 0.6 <= score < 0.65
        if selected_threshold == 0.65:
            return 0.65 <= score < 0.7
        if selected_threshold == 0.7:
            return 0.7 <= score < 0.75
        if selected_threshold == 0.75:
            return 0.75 <= score < 0.8
        if selected_threshold == 0.8:
            return 0.8 <= score < 0.9
        if selected_threshold == 0.9:
            return 0.9 <= score < 1.0
        return score >= selected_threshold

    filtered_df = cluster_df[cluster_df["similarity"].apply(is_in_threshold)].copy()
    filtered_df = filtered_df.sort_values("similarity", ascending=False).reset_index(drop=True)

    if filtered_df.empty:
        st.info("No event pairs found for the selected similarity threshold.")
        return

    table_df = filtered_df[["event1", "event2"]].copy()
    table_df = table_df.rename(columns={"event1": "Primary Event", "event2": "Secondary Event"})
    table_df.insert(0, "Select", False)

    edited_df = st.data_editor(
        table_df,
        width="stretch",
        hide_index=True,
        disabled=["Primary Event", "Secondary Event"],
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", width="small", default=False),
        },
    )

    corrected_pairs = edited_df.loc[edited_df["Select"], ["Primary Event", "Secondary Event"]].copy()

    header_col, action_col = st.columns([6, 1])
    with header_col:
        st.subheader("Need Correction")
    with action_col:
        st.write("")
        if st.button("Save", width="stretch"):
            output_dir = Path(config.locations.outputs)
            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / "events_clustering_corrections.xlsx"

            new_pairs = _canonicalize_pair_table(corrected_pairs)
            if new_pairs.empty:
                st.info("No pairs selected to save.")
            else:
                combined = pd.DataFrame(columns=["Primary Event", "Secondary Event"])
                if file_path.exists():
                    try:
                        existing = pd.read_excel(file_path)
                        if {"Primary Event", "Secondary Event"}.issubset(existing.columns):
                            combined = existing[["Primary Event", "Secondary Event"]].copy()
                    except Exception:
                        combined = pd.DataFrame(columns=["Primary Event", "Secondary Event"])

                combined = pd.concat([combined, new_pairs], ignore_index=True)
                combined = _canonicalize_pair_table(combined)
                combined.to_excel(file_path, index=False)
                _show_tooltip_message(f"Saved to {file_path}")

    st.dataframe(corrected_pairs, hide_index=True, width="stretch")


def main():
    """Entry point for the event clustering page when run directly."""
    event_clusters()


if __name__ == "__main__":
    main()
