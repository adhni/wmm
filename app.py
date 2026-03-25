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
    runner_best_by_marathon,
    runner_marathon_breakdown,
    runner_name_from_option,
    runner_options,
    runner_progression,
    runner_results,
    runner_summary,
    star_table,
    summary_metrics,
    top_repeat_runners,
    to_csv_bytes,
    yearly_leaders,
)


st.set_page_config(
    page_title="WMM",
    page_icon="🏃",
    layout="wide",
)


alt.themes.enable("default")


TIME_LABEL_EXPR = (
    "floor(datum.value/3600) + ':' + "
    "(floor((datum.value % 3600)/60) < 10 ? '0' : '') + "
    "floor((datum.value % 3600)/60)"
)


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
            y=alt.Y(
                "Median_Time_Seconds:Q",
                title="Median Finish Time",
                axis=alt.Axis(labelExpr=TIME_LABEL_EXPR),
            ),
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


def runner_progression_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3, color="#c84c2f")
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y(
                "Time_seconds:Q",
                title="Best Result By Year",
                axis=alt.Axis(labelExpr=TIME_LABEL_EXPR),
            ),
            tooltip=["Year:O", "Marathon:N", "Time:N", "Time_HHMM:N"],
        )
        .properties(height=320)
    )


def runner_breakdown_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(color="#182126", cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("Marathon:N", sort="-y", title="Marathon"),
            y=alt.Y("Entries:Q", title="Entries"),
            tooltip=["Marathon:N", "Entries:Q", "Best_Time:N", "First_Year:Q", "Latest_Year:Q"],
        )
        .properties(height=320)
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
    growth = runner_growth(filtered)
    medians = median_finish_times(filtered)
    repeats = top_repeat_runners(filtered)
    fastest_course = fastest_by_marathon(filtered)
    fastest_year = fastest_by_year(filtered)
    leaders = yearly_leaders(filtered)
    stars = star_table(filtered)

    overview_tab, runner_tab, data_tab = st.tabs(["Overview", "Runner Explorer", "Data"])

    with overview_tab:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{metrics['rows']:,}")
        c2.metric("Unique Runners", f"{metrics['runners']:,}")
        c3.metric("Marathons", metrics["marathons"])
        c4.metric("Year Range", metrics["year_range"])
        st.info(f"Fastest result in view: {metrics['fastest_label']}")
        st.download_button(
            "Download Filtered Dataset",
            data=to_csv_bytes(filtered),
            file_name="wmm_filtered.csv",
            mime="text/csv",
        )

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
            st.dataframe(repeats, use_container_width=True, hide_index=True)
        with right:
            st.subheader("Fastest By Marathon")
            st.dataframe(fastest_course, use_container_width=True, hide_index=True)

        left, right = st.columns(2)
        with left:
            st.subheader("Fastest By Year")
            st.dataframe(fastest_year, use_container_width=True, hide_index=True)
        with right:
            st.subheader("Yearly Leaders By Marathon")
            st.dataframe(leaders, use_container_width=True, hide_index=True)

    with runner_tab:
        options = runner_options(filtered)
        if not options:
            st.warning("No runners match the current filters.")
        else:
            selected_runner_option = st.selectbox(
                "Search for a runner",
                options,
                index=0,
            )
            runner_name = runner_name_from_option(selected_runner_option)
            runner_stats = runner_summary(filtered, runner_name)
            runner_df = runner_results(filtered, runner_name)
            runner_best = runner_best_by_marathon(filtered, runner_name)
            runner_progress = runner_progression(filtered, runner_name)
            runner_breakdown = runner_marathon_breakdown(filtered, runner_name)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entries", runner_stats["entries"])
            c2.metric("Stars", runner_stats["stars"])
            c3.metric("Best Time", runner_stats["best_time"])
            c4.metric("Best Result", runner_stats["best_result"])
            c5.metric("Latest Result", runner_stats["latest_result"])

            left, right = st.columns([1.2, 0.8])
            with left:
                st.subheader("Best Result By Year")
                st.altair_chart(runner_progression_chart(runner_progress), use_container_width=True)
            with right:
                st.subheader("Marathon Breakdown")
                st.altair_chart(runner_breakdown_chart(runner_breakdown), use_container_width=True)

            left, right = st.columns(2)
            with left:
                st.subheader("All Results")
                st.dataframe(runner_df, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download Runner Results",
                    data=to_csv_bytes(runner_df),
                    file_name=f"{runner_name.lower().replace(' ', '_')}_results.csv",
                    mime="text/csv",
                )
            with right:
                st.subheader("Best By Marathon")
                st.dataframe(runner_best, use_container_width=True, hide_index=True)

    with data_tab:
        st.subheader("WMM Stars By Runner")
        st.dataframe(stars, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Stars Table",
            data=to_csv_bytes(stars),
            file_name="wmm_stars.csv",
            mime="text/csv",
        )

        st.subheader("Filtered Raw Data")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption("This table reflects the marathon and year filters from the sidebar.")
        st.download_button(
            "Download Raw Data",
            data=to_csv_bytes(filtered),
            file_name="wmm_raw_filtered.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
