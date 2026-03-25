from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.wmm.data import load_data
from src.wmm.metrics import (
    fastest_by_marathon,
    fastest_by_year,
    filtered_data,
    finish_time_spectrum,
    latest_year_snapshot,
    marathon_rankings,
    median_finish_times,
    runner_best_by_marathon,
    runner_growth,
    runner_marathon_breakdown,
    runner_name_from_option,
    runner_options,
    runner_progression,
    runner_results,
    runner_summary,
    star_distribution,
    star_table,
    summary_metrics,
    to_csv_bytes,
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

MARATHON_DOMAIN = ["Berlin", "Boston", "Chicago", "London", "NYC"]
MARATHON_RANGE = ["#b33f24", "#ce7f3c", "#164b63", "#638d8b", "#221f3b"]
MARATHON_COLOR = alt.Scale(domain=MARATHON_DOMAIN, range=MARATHON_RANGE)


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_data()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(200, 76, 47, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(34, 31, 59, 0.16), transparent 26%),
                linear-gradient(180deg, #f7f1e7 0%, #f2eadc 48%, #efe3d2 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        .hero-shell {
            padding: 2rem 2.1rem;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(16, 24, 39, 0.95), rgba(34, 31, 59, 0.88));
            color: #f8f2e9;
            box-shadow: 0 28px 70px rgba(34, 31, 59, 0.16);
            margin-bottom: 1rem;
        }
        .hero-kicker {
            letter-spacing: 0.24em;
            font-size: 0.78rem;
            text-transform: uppercase;
            color: #f0be7a;
            margin-bottom: 0.9rem;
        }
        .hero-title {
            font-size: 2.8rem;
            line-height: 0.95;
            margin: 0 0 0.8rem 0;
            max-width: 10ch;
        }
        .hero-copy {
            max-width: 55rem;
            color: rgba(248, 242, 233, 0.82);
            font-size: 1rem;
            line-height: 1.55;
            margin-bottom: 1rem;
        }
        .hero-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 1.3rem;
        }
        .hero-chip {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(248, 242, 233, 0.08);
            border: 1px solid rgba(248, 242, 233, 0.1);
        }
        .hero-chip-label {
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(248, 242, 233, 0.62);
            margin-bottom: 0.35rem;
        }
        .hero-chip-value {
            font-size: 1.05rem;
            color: #f8f2e9;
        }
        .section-kicker {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.76rem;
            color: #7a4c2f;
            margin-bottom: 0.25rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid rgba(34, 31, 59, 0.08);
            padding: 1rem 1rem 0.8rem 1rem;
            border-radius: 18px;
            box-shadow: 0 15px 32px rgba(34, 31, 59, 0.06);
        }
        div[data-testid="stMetricLabel"] {
            color: #6b5563;
        }
        div[data-testid="stMetricValue"] {
            color: #182126;
        }
        div[data-testid="stTabs"] button {
            font-weight: 600;
        }
        .stDataFrame, div[data-testid="stTable"] {
            border-radius: 16px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f"<div class='section-kicker'>{text}</div>", unsafe_allow_html=True)


def render_hero(metrics: dict[str, str | int], selected_marathons: list[str], selected_years: tuple[int, int]) -> None:
    marathon_text = " / ".join(selected_marathons)
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-kicker">World Marathon Majors • Indonesia</div>
            <div class="hero-title">A richer pulse on Indonesian marathon travel.</div>
            <div class="hero-copy">
                This view tracks <strong>{metrics['rows']:,}</strong> finishes across
                <strong>{selected_years[0]}-{selected_years[1]}</strong>, blending volume,
                speed, repeat participation, and runner-level progression instead of
                stopping at static summary tables.
            </div>
            <div class="hero-strip">
                <div class="hero-chip">
                    <div class="hero-chip-label">Marathons In View</div>
                    <div class="hero-chip-value">{marathon_text}</div>
                </div>
                <div class="hero-chip">
                    <div class="hero-chip-label">Latest Year Pulse</div>
                    <div class="hero-chip-value">{metrics['latest_year']} • {metrics['latest_entries']:,} finishes</div>
                </div>
                <div class="hero-chip">
                    <div class="hero-chip-label">Fastest Result In View</div>
                    <div class="hero-chip-value">{metrics['fastest_label']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def growth_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y("Runner_Count:Q", title="Runner Count"),
            color=alt.Color("Marathon:N", scale=MARATHON_COLOR, title="Marathon"),
            tooltip=["Year:O", "Marathon:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=340)
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
            color=alt.Color("Marathon:N", scale=MARATHON_COLOR, title="Marathon"),
            tooltip=[
                "Year:O",
                "Marathon:N",
                "Median_Time_HHMM:N",
                alt.Tooltip("Median_Time_Seconds:Q", format=",.0f"),
            ],
        )
        .properties(height=340)
    )


def snapshot_chart(data: pd.DataFrame, latest_year: int) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10)
        .encode(
            x=alt.X("Marathon:N", sort="-y", title=None),
            y=alt.Y("Runner_Count:Q", title=f"Runner Count in {latest_year}"),
            color=alt.Color("Marathon:N", scale=MARATHON_COLOR, legend=None),
            tooltip=[
                "Marathon:N",
                alt.Tooltip("Runner_Count:Q", format=",.0f"),
                "Median_Time:N",
                "Fastest_Time:N",
            ],
        )
        .properties(height=320)
    )


def ranking_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y(
                "Rank:Q",
                title="Popularity Rank",
                scale=alt.Scale(domain=[len(MARATHON_DOMAIN), 1]),
            ),
            color=alt.Color("Marathon:N", scale=MARATHON_COLOR, title="Marathon"),
            tooltip=["Year:O", "Marathon:N", "Rank:Q", "Runner_Count:Q"],
        )
        .properties(height=320)
    )


def heatmap_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_rect(cornerRadius=6)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y("Marathon:N", title=None, sort=MARATHON_DOMAIN),
            color=alt.Color("Runner_Count:Q", title="Runner Count", scale=alt.Scale(scheme="goldred")),
            tooltip=["Year:O", "Marathon:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=280)
    )


def spectrum_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_rect()
        .encode(
            x=alt.X("Time_Bin:N", title="Finish Time Spectrum", sort=list(data["Time_Bin"].unique())),
            y=alt.Y("Marathon:N", title=None, sort=MARATHON_DOMAIN),
            color=alt.Color("Runner_Count:Q", title="Runner Count", scale=alt.Scale(scheme="teals")),
            tooltip=["Marathon:N", "Time_Bin:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=280)
    )


def star_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10, color="#221f3b")
        .encode(
            x=alt.X("Stars:O", title="Unique Majors Completed"),
            y=alt.Y("Runner_Count:Q", title="Runner Count"),
            tooltip=["Stars:O", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=260)
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
            tooltip=["Year:O", "Marathon:N", "Time:N", "Time_HHMM:N", "Indo_Place:Q"],
        )
        .properties(height=320)
    )


def runner_rank_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_circle(size=140, opacity=0.85)
        .encode(
            x=alt.X("Year:O", title="Year"),
            y=alt.Y("Indo_Place:Q", title="Indonesian Rank", scale=alt.Scale(reverse=True)),
            color=alt.Color("Marathon:N", scale=MARATHON_COLOR, title="Marathon"),
            tooltip=["Year:O", "Marathon:N", "Time:N", "Indo_Place:Q", "Place:Q"],
        )
        .properties(height=320)
    )


def runner_breakdown_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10, color="#182126")
        .encode(
            x=alt.X("Marathon:N", sort="-y", title=None),
            y=alt.Y("Entries:Q", title="Entries"),
            tooltip=["Marathon:N", "Entries:Q", "Best_Time:N", "First_Year:Q", "Latest_Year:Q"],
        )
        .properties(height=320)
    )


def main() -> None:
    inject_css()

    df = get_data()
    marathons = sorted(df["Marathon"].unique())
    year_min = int(df["Year"].min())
    year_max = int(df["Year"].max())

    with st.sidebar:
        st.header("Lens")
        selected_marathons = st.multiselect("Marathons", marathons, default=marathons)
        selected_years = st.slider(
            "Year range",
            min_value=year_min,
            max_value=year_max,
            value=(max(2015, year_min), year_max),
        )
        time_bin_minutes = st.select_slider(
            "Spectrum bin size",
            options=[10, 15, 20, 30],
            value=15,
        )
        st.caption("Use a tighter bin for more texture in the finish-time spectrum.")

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
    ranking = marathon_rankings(filtered)
    spectrum = finish_time_spectrum(filtered, bin_minutes=time_bin_minutes)
    stars_by_count = star_distribution(filtered)
    fastest_course = fastest_by_marathon(filtered)
    fastest_year = fastest_by_year(filtered)
    latest_year, latest_snapshot = latest_year_snapshot(filtered)
    stars = star_table(filtered)

    render_hero(metrics, selected_marathons, selected_years)

    metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)
    metric_1.metric("Finishes", f"{metrics['rows']:,}")
    metric_2.metric("Unique Runners", f"{metrics['runners']:,}")
    metric_3.metric("Marathons", metrics["marathons"])
    metric_4.metric(
        f"{metrics['latest_year']} Entries",
        f"{metrics['latest_entries']:,}",
        delta=f"{metrics['entry_delta']:+,}",
    )
    metric_5.metric("View Range", metrics["year_range"])

    pulse_tab, compare_tab, runner_tab, data_tab = st.tabs(
        ["Pulse", "Compare", "Runner Lab", "Data Vault"]
    )

    with pulse_tab:
        left, right = st.columns([1.05, 0.95])
        with left:
            section_label("Latest-Year Snapshot")
            st.subheader(f"Who owned the latest visible edition: {latest_year}")
            st.altair_chart(snapshot_chart(latest_snapshot, latest_year), use_container_width=True)
        with right:
            section_label("Popularity Drift")
            st.subheader("Marathon rank changes over time")
            st.altair_chart(ranking_chart(ranking), use_container_width=True)

        left, right = st.columns(2)
        with left:
            section_label("Heat Map")
            st.subheader("Participation density by year and course")
            st.altair_chart(heatmap_chart(growth), use_container_width=True)
        with right:
            section_label("Stars")
            st.subheader("How many majors most runners have touched")
            st.altair_chart(star_chart(stars_by_count), use_container_width=True)

    with compare_tab:
        left, right = st.columns(2)
        with left:
            section_label("Volume")
            st.subheader("Participation growth")
            st.altair_chart(growth_chart(growth), use_container_width=True)
        with right:
            section_label("Speed")
            st.subheader("Median finish time trajectory")
            st.altair_chart(median_chart(medians), use_container_width=True)

        section_label("Spectrum")
        st.subheader("Finish-time texture by marathon")
        st.altair_chart(spectrum_chart(spectrum), use_container_width=True)

        left, right = st.columns(2)
        with left:
            section_label("Course Leaders")
            st.subheader("Fastest result on each course")
            st.dataframe(fastest_course, use_container_width=True, hide_index=True)
        with right:
            section_label("Season Leaders")
            st.subheader("Fastest visible runner by year")
            st.dataframe(fastest_year, use_container_width=True, hide_index=True)

    with runner_tab:
        options = runner_options(filtered)
        if not options:
            st.warning("No runners match the current filters.")
        else:
            selected_runner_option = st.selectbox("Search runner", options, index=0)
            runner_name = runner_name_from_option(selected_runner_option)
            runner_stats = runner_summary(filtered, runner_name)
            runner_df = runner_results(filtered, runner_name)
            runner_best = runner_best_by_marathon(filtered, runner_name)
            runner_progress = runner_progression(filtered, runner_name)
            runner_breakdown = runner_marathon_breakdown(filtered, runner_name)

            st.markdown(f"## {runner_name}")
            st.caption("Individual runner view with progression, Indonesian rank, and course spread.")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entries", runner_stats["entries"])
            c2.metric("Stars", runner_stats["stars"])
            c3.metric("Years Active", runner_stats["years_active"])
            c4.metric("Best Time", runner_stats["best_time"])
            c5.metric("Latest Result", runner_stats["latest_result"])
            st.info(f"Peak result: {runner_stats['best_result']}")

            left, right = st.columns(2)
            with left:
                section_label("Progression")
                st.subheader("Best result by year")
                st.altair_chart(runner_progression_chart(runner_progress), use_container_width=True)
            with right:
                section_label("Rank")
                st.subheader("Indonesian placing by race")
                st.altair_chart(runner_rank_chart(runner_df), use_container_width=True)

            left, right = st.columns([0.85, 1.15])
            with left:
                section_label("Course Mix")
                st.subheader("Where this runner keeps showing up")
                st.altair_chart(runner_breakdown_chart(runner_breakdown), use_container_width=True)
            with right:
                section_label("Career Log")
                st.subheader("All visible results")
                st.dataframe(runner_df, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download Runner Log",
                    data=to_csv_bytes(runner_df),
                    file_name=f"{runner_name.lower().replace(' ', '_')}_results.csv",
                    mime="text/csv",
                )

            section_label("Best Splits")
            st.subheader("Best result by marathon")
            st.dataframe(runner_best, use_container_width=True, hide_index=True)

    with data_tab:
        section_label("Downloads")
        st.subheader("Take the filtered dataset out of the app")
        st.download_button(
            "Download Filtered Dataset",
            data=to_csv_bytes(filtered),
            file_name="wmm_filtered.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download Stars Table",
            data=to_csv_bytes(stars),
            file_name="wmm_stars.csv",
            mime="text/csv",
        )

        left, right = st.columns(2)
        with left:
            section_label("Stars Table")
            st.subheader("Runner-by-runner major coverage")
            st.dataframe(stars, use_container_width=True, hide_index=True)
        with right:
            section_label("Raw View")
            st.subheader("Filtered raw data")
            st.dataframe(filtered, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
