import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _load_spell_check_rows():
    input_dir = Path(config.locations.inputs)
    workbook_path = input_dir / "service_event_inconsistencies.xlsx"

    if not workbook_path.exists():
        st.error(f"Workbook not found: {workbook_path}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(workbook_path, sheet_name="Spell Check")
    except ValueError:
        st.error("The workbook does not contain the 'Spell Check' sheet.")
        return pd.DataFrame()

    required_cols = {"event", "misspelled_words", "review_required"}
    missing_cols = required_cols.difference(df.columns)
    if missing_cols:
        st.error(f"The 'Spell Check' sheet is missing required columns: {sorted(missing_cols)}")
        return pd.DataFrame()

    filtered_df = df.loc[df["review_required"].astype(bool), ["event", "misspelled_words"]].copy()
    filtered_df = filtered_df.rename(columns={"event": "Event", "misspelled_words": "Misspelled Words"})
    return filtered_df.reset_index(drop=True)


def misspelt_events():
    st.title("Misspelt Events")
    st.write("Service Events that are potentially misspelt are identified.")

    spell_check_df = _load_spell_check_rows()
    if spell_check_df.empty:
        st.info("No events need review in the Spell Check sheet.")
        return

    split_index = max(1, len(spell_check_df) // 2)
    left_df = spell_check_df.iloc[:split_index].reset_index(drop=True)
    right_df = spell_check_df.iloc[split_index:].reset_index(drop=True)

    left_col, right_col = st.columns(2)

    with left_col:
        st.dataframe(left_df, use_container_width=True, hide_index=True, height=520)

    with right_col:
        st.dataframe(right_df, use_container_width=True, hide_index=True, height=520)


def main():
    misspelt_events()


if __name__ == "__main__":
    main()
