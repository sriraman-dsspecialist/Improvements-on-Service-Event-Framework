import sys
import textwrap
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import config


def _load_service_event_orders():
    input_dir = Path(config.locations.inputs)
    file_path = input_dir / "ServiceEvent_Order_Count.xlsx"
    if not file_path.exists():
        raise FileNotFoundError(f"Service event order count file not found: {file_path}")

    df = pd.read_excel(file_path)
    required_columns = {"ServiceEventName", "Year", "count_orders"}
    missing = required_columns.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {sorted(missing)}")

    df = df.copy()
    df["ServiceEventName"] = df["ServiceEventName"].astype(str).str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["count_orders"] = pd.to_numeric(df["count_orders"], errors="coerce").fillna(0)
    df = df.dropna(subset=["ServiceEventName", "Year"]).copy()
    df["Year"] = df["Year"].astype(int)
    return df.sort_values(["Year", "ServiceEventName"]).reset_index(drop=True)


def _wrap_legend_label(name: str, width: int = 24) -> str:
    return "<br>".join(textwrap.wrap(str(name), width=width))


def _event_timeline_long(event_names, event_df: pd.DataFrame, wrap_legend: bool = True) -> pd.DataFrame:
    valid_names = [name for name in event_names if name in set(event_df["ServiceEventName"])]
    if not valid_names:
        return pd.DataFrame(columns=["Year", "ServiceEventName", "LegendLabel", "Order Count"])

    all_years = sorted(event_df["Year"].dropna().unique().tolist())
    full_index = pd.MultiIndex.from_product([all_years, valid_names], names=["Year", "ServiceEventName"])
    filtered = event_df[event_df["ServiceEventName"].isin(valid_names)][["Year", "ServiceEventName", "count_orders"]].copy()
    filtered["count_orders"] = pd.to_numeric(filtered["count_orders"], errors="coerce").fillna(0)

    complete_df = (
        filtered.groupby(["Year", "ServiceEventName"], as_index=False)["count_orders"]
        .sum()
        .set_index(["Year", "ServiceEventName"])
        .reindex(full_index)
        .fillna(0)
        .reset_index()
        .rename(columns={"count_orders": "Order Count"})
    )

    if wrap_legend:
        complete_df["LegendLabel"] = complete_df["ServiceEventName"].map(_wrap_legend_label)
    else:
        complete_df["LegendLabel"] = complete_df["ServiceEventName"]

    return complete_df


def _prepare_year_ranking_df(event_df: pd.DataFrame, year: int, ascending: bool, limit: int = 5) -> pd.DataFrame:
    year_df = (
        event_df[event_df["Year"] == year]
        .groupby("ServiceEventName", as_index=False)["count_orders"]
        .sum()
        .rename(columns={"count_orders": "Order Count"})
    )
    ranked_df = (
        year_df.sort_values(["Order Count", "ServiceEventName"], ascending=[ascending, True])
        .head(limit)
        .reset_index(drop=True)
    )
    ranked_df["LegendLabel"] = ranked_df["ServiceEventName"].map(_wrap_legend_label)
    ranked_df["BubbleSize"] = ranked_df["Order Count"].clip(lower=1)
    return ranked_df


def _build_event_bubble_chart(chart_df: pd.DataFrame, dot_color: str = "#2563eb", height: int = 400):
    category_order = chart_df["LegendLabel"].tolist()
    fig = px.scatter(
        chart_df,
        x="LegendLabel",
        y="Order Count",
        size="BubbleSize",
        size_max=42,
        category_orders={"LegendLabel": category_order},
        hover_name="ServiceEventName",
        hover_data={"LegendLabel": False, "BubbleSize": False, "Order Count": ":,"},
    )
    fig.update_traces(marker=dict(color=dot_color, opacity=0.85, sizemin=14))
    fig.update_layout(
        height=height,
        showlegend=False,
        xaxis=dict(title=None, categoryorder="array", categoryarray=category_order),
        yaxis=dict(title="Order Count"),
        margin=dict(l=20, r=20, t=20, b=60),
    )
    return fig


def _build_timeline_bubble_chart(chart_df: pd.DataFrame, dot_color: str = "#10b981", height: int = 440):
    plot_df = chart_df.copy()
    plot_df["BubbleSize"] = plot_df["Order Count"].clip(lower=1)
    fig = px.scatter(
        plot_df,
        x="Year",
        y="Order Count",
        size="BubbleSize",
        size_max=40,
        hover_name="ServiceEventName",
        hover_data={"LegendLabel": False, "BubbleSize": False, "Year": True, "Order Count": ":,"},
    )
    fig.update_traces(marker=dict(color=dot_color, opacity=0.85, sizemin=12))
    fig.update_layout(
        height=height,
        showlegend=False,
        xaxis=dict(title="Year", dtick=1),
        yaxis=dict(title="Order Count"),
        margin=dict(l=20, r=20, t=20, b=40),
    )
    return fig


def event_distribution():
    st.title("Distribution of Service Events")
    st.write("Count of Service Orders over Service Events x Year")

    event_df = _load_service_event_orders()
    available_years = sorted(event_df["Year"].unique().tolist(), reverse=True)
    default_year = available_years[0]

    col_left, col_right = st.columns(2)

    with col_left:
        left_year = st.selectbox(
            "Select year for highest order counts",
            options=available_years,
            index=0,
            key="highest_order_year_selector",
            label_visibility="collapsed",
        )
        st.subheader(f"Top 5 highest order counts in {left_year}")
        st.caption(f"Showing the 5 service events with the highest order volumes in {left_year}.")
        left_chart_df = _prepare_year_ranking_df(event_df, left_year, ascending=False, limit=5)
        st.plotly_chart(_build_event_bubble_chart(left_chart_df, dot_color="#2563eb"), use_container_width=True)

    with col_right:
        right_year = st.selectbox(
            "Select year for lowest order counts",
            options=available_years,
            index=0,
            key="lowest_order_year_selector",
            label_visibility="collapsed",
        )
        st.subheader(f"Top 5 lowest order counts in {right_year}")
        st.caption(f"Showing the 5 service events with the lowest order volumes in {right_year}.")
        right_chart_df = _prepare_year_ranking_df(event_df, right_year, ascending=True, limit=5)
        st.plotly_chart(_build_event_bubble_chart(right_chart_df, dot_color="#ef4444"), use_container_width=True)

    st.divider()
    st.subheader("Service Event Trend Explorer")

    event_names = sorted(event_df["ServiceEventName"].dropna().unique().tolist())
    latest_top_df = event_df[event_df["Year"] == default_year].sort_values("count_orders", ascending=False)
    default_event = latest_top_df.iloc[0]["ServiceEventName"] if not latest_top_df.empty else event_names[0]

    if hasattr(st, "autocomplete"):
        if "service_event_autocomplete" not in st.session_state:
            st.session_state["service_event_autocomplete"] = default_event
        selected_event = st.autocomplete(
            label="Type or select a service event",
            options=event_names,
            key="service_event_autocomplete",
            label_visibility="collapsed",
        )
        if not selected_event:
            selected_event = default_event
    else:
        selected_event = st.selectbox(
            "Type or select a service event",
            options=event_names,
            index=event_names.index(default_event),
            label_visibility="collapsed",
        )

    explorer_df = _event_timeline_long([selected_event], event_df, wrap_legend=True)
    st.plotly_chart(_build_timeline_bubble_chart(explorer_df, dot_color="#10b981", height=440), use_container_width=True)


def main():
    event_distribution()


if __name__ == "__main__":
    main()

