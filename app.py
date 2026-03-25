from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.wmm.data import load_data
from src.wmm.metrics import (
    fastest_by_marathon,
    fastest_by_year,
    filtered_data,
    median_finish_times,
    runner_growth,
    star_table,
    summary_metrics,
    top_repeat_runners,
    yearly_leaders,
)


st.set_page_config(
    page_title="WMM",
    page_icon="🏃",
    layout="wide",
)


alt.themes.enable("default")


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_data()


def line_chart(data: pd.DataFrame, y_field: str, y_title: str) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            color=alt.Color("Marathon:N", title="Marathon"),
            tooltip=["Year:O", "Marathon:N", alt.Tooltip(f"{y_field}:Q", format=",.0f")],
        )
        .properties(height=360)
    )


def median_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y("Median_Time_Seconds:Q", title="Median Finish Time (seconds)"),
            color=alt.Color("Marathon:N", title="Marathon"),
            tooltip=[
                "Year:O",
                "Marathon:N",
                "Median_Time_HHMM:N",
                alt.Tooltip("Median_Time_Seconds:Q", format=",.0f"),
            ],
        )
        .properties(height=360)
    )


def main() -> None:
    df = get_data()
    marathons = sorted(df["Marathon"].unique())
    year_min = int(df["Year"].min())
    year_max = int(df["Year"].max())

    st.title("Indonesian Runners in the World Marathon Majors")
    st.caption("Streamlit Community Cloud ready. Built from the WMM dataset in this repo.")

    with st.sidebar:
        st.header("Filters")
        selected_marathons = st.multiselect(
            "Marathons",
            marathons,
            default=marathons,
        )
        selected_years = st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            value=(max(2015, year_min), year_max),
        )

    if not selected_marathons:
        st.warning("Select at least one marathon.")
        return

    filtered = filtered_data(
        df,
        selected_marathons=selected_marathons,
        year_min=selected_years[0],
        year_max=selected_years[1],
    )

    if filtered.empty:
        st.warning("No rows match the current filters.")
        return

    metrics = summary_metrics(filtered)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{metrics['rows']:,}")
    c2.metric("Unique Runners", f"{metrics['runners']:,}")
    c3.metric("Marathons", metrics["marathons"])
    c4.metric("Year Range", metrics["year_range"])
    st.info(f"Fastest result in view: {metrics['fastest_label']}")

    growth = runner_growth(filtered)
    medians = median_finish_times(filtered)

    left, right = st.columns(2)
    with left:
        st.subheader("Participation Growth")
        st.altair_chart(line_chart(growth, "Runner_Count", "Runner Count"), use_container_width=True)
    with right:
        st.subheader("Median Finish Time")
        st.altair_chart(median_chart(medians), use_container_width=True)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.subheader("Top Repeat Runners")
        st.dataframe(top_repeat_runners(filtered), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Fastest By Marathon")
        st.dataframe(fastest_by_marathon(filtered), use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Fastest By Year")
        st.dataframe(fastest_by_year(filtered), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Yearly Leaders By Marathon")
        st.dataframe(yearly_leaders(filtered), use_container_width=True, hide_index=True)

    st.subheader("WMM Stars By Runner")
    st.dataframe(star_table(filtered), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
