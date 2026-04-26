from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from src.wmm.cards import (
    runner_goals_card,
    runner_milestones_card,
    runner_passport_card,
    runner_year_review_card,
)
from src.wmm.data import load_data
from src.wmm.metrics import (
    active_years_leaderboard,
    entry_leaderboard,
    fastest_by_marathon,
    fastest_by_year,
    filtered_data,
    finish_time_spectrum,
    hall_of_fame_cards,
    improvement_leaderboard,
    latest_year_snapshot,
    marathon_rankings,
    marathon_profile_summary,
    marathon_top_performers,
    median_finish_times,
    missing_major_pressure,
    road_to_stars,
    runner_best_by_marathon,
    runner_badges,
    runner_growth,
    runner_marathon_breakdown,
    runner_milestones,
    runner_option_labels,
    runner_next_goals,
    runner_search_options,
    runner_personal_story,
    runner_progression,
    runner_rarity_summary,
    runner_results,
    runner_summary,
    runner_year_in_review,
    star_leaderboard,
    star_status_summary,
    star_distribution,
    star_table,
    sub4_leaderboard,
    summary_metrics,
    to_csv_bytes,
)


st.set_page_config(
    page_title="WMM",
    page_icon="🏃",
    layout="wide",
)


alt.theme.enable("default")


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
        .badge-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(34, 31, 59, 0.08);
            box-shadow: 0 15px 30px rgba(34, 31, 59, 0.06);
            min-height: 138px;
            margin-bottom: 0.75rem;
        }
        .badge-title {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #8a5a34;
            margin-bottom: 0.55rem;
        }
        .badge-winner {
            font-size: 1.1rem;
            font-weight: 700;
            color: #182126;
            line-height: 1.15;
            margin-bottom: 0.45rem;
        }
        .badge-detail {
            color: #5d5260;
            line-height: 1.45;
        }
        .story-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(34, 31, 59, 0.06);
            border: 1px solid rgba(34, 31, 59, 0.08);
            margin-bottom: 1rem;
            color: #2a2a2a;
            line-height: 1.55;
        }
        .passport-card {
            padding: 1.45rem 1.5rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(200, 76, 47, 0.92), rgba(34, 31, 59, 0.9));
            color: #f8f2e9;
            box-shadow: 0 24px 55px rgba(34, 31, 59, 0.15);
            margin-bottom: 1rem;
        }
        .passport-kicker {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.75rem;
            color: rgba(248, 242, 233, 0.7);
            margin-bottom: 0.55rem;
        }
        .passport-name {
            font-size: 2rem;
            line-height: 1;
            margin-bottom: 0.75rem;
        }
        .passport-copy {
            max-width: 58rem;
            color: rgba(248, 242, 233, 0.86);
            line-height: 1.55;
            margin-bottom: 1rem;
        }
        .passport-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.75rem;
        }
        .passport-stat {
            padding: 0.9rem 0.95rem;
            border-radius: 16px;
            background: rgba(248, 242, 233, 0.08);
            border: 1px solid rgba(248, 242, 233, 0.1);
        }
        .passport-stat-label {
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: rgba(248, 242, 233, 0.66);
            margin-bottom: 0.3rem;
        }
        .passport-stat-value {
            color: #f8f2e9;
            line-height: 1.35;
        }
        .goal-card {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(34, 31, 59, 0.08);
            box-shadow: 0 15px 30px rgba(34, 31, 59, 0.05);
            min-height: 155px;
            margin-bottom: 0.75rem;
        }
        .goal-card-title {
            font-size: 0.76rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #8a5a34;
            margin-bottom: 0.55rem;
        }
        .goal-card-target {
            font-size: 1.15rem;
            color: #182126;
            font-weight: 700;
            margin-bottom: 0.35rem;
            line-height: 1.2;
        }
        .goal-card-gap {
            color: #c84c2f;
            font-weight: 600;
            margin-bottom: 0.45rem;
        }
        .goal-card-why {
            color: #5d5260;
            line-height: 1.45;
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


def render_badge_card(title: str, winner: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="badge-card">
            <div class="badge-title">{title}</div>
            <div class="badge-winner">{winner}</div>
            <div class="badge-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_card(text: str) -> None:
    st.markdown(f"<div class='story-card'>{text}</div>", unsafe_allow_html=True)


def render_passport_card(
    runner_name: str,
    summary: dict[str, str | int],
    road_row: pd.Series,
    story: str,
) -> None:
    st.markdown(
        f"""
        <div class="passport-card">
            <div class="passport-kicker">My WMM Passport</div>
            <div class="passport-name">{runner_name}</div>
            <div class="passport-copy">{story}</div>
            <div class="passport-grid">
                <div class="passport-stat">
                    <div class="passport-stat-label">Completed</div>
                    <div class="passport-stat-value">{road_row['Completed_Majors']}</div>
                </div>
                <div class="passport-stat">
                    <div class="passport-stat-label">Missing</div>
                    <div class="passport-stat-value">{road_row['Missing_Majors']}</div>
                </div>
                <div class="passport-stat">
                    <div class="passport-stat-label">Best Result</div>
                    <div class="passport-stat-value">{summary['best_result']}</div>
                </div>
                <div class="passport-stat">
                    <div class="passport-stat-label">Favorite Course</div>
                    <div class="passport-stat-value">{summary['favorite_marathon']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_goal_card(goal: str, target: str, gap: str, why: str) -> None:
    st.markdown(
        f"""
        <div class="goal-card">
            <div class="goal-card-title">{goal}</div>
            <div class="goal-card-target">{target}</div>
            <div class="goal-card-gap">{gap}</div>
            <div class="goal-card-why">{why}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_personal_badge(title: str, detail: str) -> None:
    render_badge_card(title, "Unlocked", detail)


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


def status_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10)
        .encode(
            x=alt.X("Status:N", title=None, sort=list(data["Status"])),
            y=alt.Y("Runner_Count:Q", title="Runner Count"),
            color=alt.Color("Status:N", legend=None, scale=alt.Scale(
                domain=["Complete", "One away", "In striking distance", "Building"],
                range=["#164b63", "#c84c2f", "#ce7f3c", "#8d7e6d"],
            )),
            tooltip=["Status:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=280)
    )


def missing_major_chart(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10, color="#c84c2f")
        .encode(
            x=alt.X("Marathon:N", sort="-y", title=None),
            y=alt.Y("Runner_Count:Q", title="One-Away Runners"),
            tooltip=["Marathon:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=280)
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


def marathon_distribution_chart(data: pd.DataFrame, marathon: str) -> alt.Chart:
    marathon_data = data.loc[data["Marathon"] == marathon]
    return (
        alt.Chart(marathon_data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color="#b33f24")
        .encode(
            x=alt.X("Time_Bin:N", title="Finish Time Band", sort=list(marathon_data["Time_Bin"].unique())),
            y=alt.Y("Runner_Count:Q", title="Runner Count"),
            tooltip=["Time_Bin:N", alt.Tooltip("Runner_Count:Q", format=",.0f")],
        )
        .properties(height=320)
    )


def profile_narrative(summary: dict[str, str | int | float], marathon: str) -> str:
    return (
        f"{marathon} shows {summary['entries']:,} visible finishes from "
        f"{summary['unique_runners']:,} unique runners in the current lens. "
        f"The latest visible edition in {summary['latest_year']} drew {summary['latest_count']:,} Indonesians, "
        f"the median finish sat at {summary['median_time']}, and {summary['repeat_share']}% of runners on this course "
        f"have shown up more than once. {summary['multi_star_share']}% of its runners are already on a 3-star-or-better journey."
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
    roadmap = road_to_stars(filtered, selected_marathons)
    roadmap_status = star_status_summary(roadmap)
    missing_pressure = missing_major_pressure(roadmap)
    badge_cards = hall_of_fame_cards(filtered)
    entry_board = entry_leaderboard(filtered)
    stars_board = star_leaderboard(filtered)
    active_board = active_years_leaderboard(filtered)
    sub4_board = sub4_leaderboard(filtered)
    improvement_board = improvement_leaderboard(filtered)
    fastest_course = fastest_by_marathon(filtered)
    fastest_year = fastest_by_year(filtered)
    latest_year, latest_snapshot = latest_year_snapshot(filtered)
    stars = star_table(filtered)
    profile_marathon = st.session_state.get("profile_marathon", selected_marathons[0])
    if profile_marathon not in selected_marathons:
        profile_marathon = selected_marathons[0]
    profile_summary_data = marathon_profile_summary(filtered, profile_marathon)
    profile_growth = growth.loc[growth["Marathon"] == profile_marathon]
    profile_medians = medians.loc[medians["Marathon"] == profile_marathon]
    profile_top = marathon_top_performers(filtered, profile_marathon)

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

    render_story_card(
        "Start with Runner Lab. It now searches the full dataset by partial name, so you can type a first name like ADHNI and jump straight to the personal view."
    )

    runner_tab, pulse_tab, stars_tab, fame_tab, profiles_tab, compare_tab, data_tab = st.tabs(
        ["Runner Lab", "Pulse", "Stars", "Hall of Fame", "Marathon Profiles", "Compare", "Data Vault"]
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

    with stars_tab:
        complete_count = int((roadmap["Status"] == "Complete").sum())
        one_away_count = int((roadmap["Status"] == "One away").sum())
        close_count = int((roadmap["Status"] == "In striking distance").sum())
        median_stars = float(roadmap["Stars"].median()) if not roadmap.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Complete", complete_count)
        c2.metric("One Away", one_away_count)
        c3.metric("In Striking Distance", close_count)
        c4.metric("Median Stars", f"{median_stars:.1f}")

        render_story_card(
            "This section treats stars as a journey inside the current filter lens. "
            "It surfaces who has finished the set, who is one race away, and which course is the most common missing final piece."
        )

        left, right = st.columns(2)
        with left:
            section_label("Journey Status")
            st.subheader("How close runners are to completing the visible set")
            st.altair_chart(status_chart(roadmap_status), use_container_width=True)
        with right:
            section_label("Final Missing Step")
            st.subheader("Which marathon 4-star runners still need")
            if missing_pressure.empty:
                st.info("No one-away runners in the current filter.")
            else:
                st.altair_chart(missing_major_chart(missing_pressure), use_container_width=True)

        left, right = st.columns([0.95, 1.05])
        with left:
            section_label("One Away")
            st.subheader("Runners who are one major from completion")
            one_away = roadmap.loc[roadmap["Status"] == "One away"]
            if one_away.empty:
                st.info("No one-away runners in the current filter.")
            else:
                st.dataframe(
                    one_away[["Name", "Entries", "WMM_PB", "Latest_Year", "Missing_Majors"]],
                    width="stretch",
                    hide_index=True,
                )
        with right:
            section_label("Road Map")
            st.subheader("Full road-to-stars table")
            st.dataframe(
                roadmap[["Name", "Stars", "Status", "Entries", "WMM_PB", "Completed_Majors", "Missing_Majors", "Latest_Year"]],
                width="stretch",
                hide_index=True,
            )
            st.download_button(
                "Download Road To Stars",
                data=to_csv_bytes(roadmap),
                file_name="wmm_road_to_stars.csv",
                mime="text/csv",
            )

    with fame_tab:
        section_label("Badge Winners")
        st.subheader("Who owns the current bragging rights")
        badge_columns = st.columns(3)
        for idx, card in enumerate(badge_cards):
            with badge_columns[idx % 3]:
                render_badge_card(card["title"], card["winner"], card["detail"])

        render_story_card(
            "These leaderboards stay grounded in the visible dataset: not just raw speed, but travel depth, staying power, consistency, and improvement."
        )

        left, right = st.columns(2)
        with left:
            section_label("Travel Depth")
            st.subheader("Most entries and most stars")
            st.dataframe(entry_board, width="stretch", hide_index=True)
            st.dataframe(stars_board, width="stretch", hide_index=True)
        with right:
            section_label("Durability")
            st.subheader("Most active years and sub-4 leaders")
            st.dataframe(active_board, width="stretch", hide_index=True)
            if sub4_board.empty:
                st.info("No sub-4 finishes in the current filter.")
            else:
                st.dataframe(sub4_board, width="stretch", hide_index=True)

        section_label("Improvement")
        st.subheader("Biggest jumps from first visible year to best visible result")
        if improvement_board.empty:
            st.info("No measurable multi-race improvements in the current filter.")
        else:
            st.dataframe(improvement_board, width="stretch", hide_index=True)

    with profiles_tab:
        section_label("Course Identity")
        st.subheader("Profile one major at a time")
        profile_marathon = st.selectbox(
            "Choose a marathon profile",
            selected_marathons,
            index=selected_marathons.index(profile_marathon),
            key="profile_marathon",
        )
        profile_summary_data = marathon_profile_summary(filtered, profile_marathon)
        profile_growth = growth.loc[growth["Marathon"] == profile_marathon]
        profile_medians = medians.loc[medians["Marathon"] == profile_marathon]
        profile_top = marathon_top_performers(filtered, profile_marathon)

        render_story_card(profile_narrative(profile_summary_data, profile_marathon))

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Entries", f"{profile_summary_data['entries']:,}")
        c2.metric("Unique Runners", f"{profile_summary_data['unique_runners']:,}")
        c3.metric(f"{profile_summary_data['latest_year']} Entries", f"{profile_summary_data['latest_count']:,}")
        c4.metric("Repeat Share", f"{profile_summary_data['repeat_share']}%")
        c5.metric("3+ Star Share", f"{profile_summary_data['multi_star_share']}%")
        st.info(
            f"Fastest visible runner on {profile_marathon}: "
            f"{profile_summary_data['fastest_runner']} in {profile_summary_data['fastest_time']}."
        )

        left, right = st.columns(2)
        with left:
            section_label("Volume")
            st.subheader("Participation over time")
            st.altair_chart(growth_chart(profile_growth), use_container_width=True)
        with right:
            section_label("Speed")
            st.subheader("Median finish-time shape")
            st.altair_chart(median_chart(profile_medians), use_container_width=True)

        section_label("Distribution")
        st.subheader("Where this marathon's runners tend to land")
        st.altair_chart(marathon_distribution_chart(spectrum, profile_marathon), use_container_width=True)

        section_label("Top Performers")
        st.subheader("Fastest visible results on this course")
        st.dataframe(profile_top, width="stretch", hide_index=True)

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
            st.dataframe(fastest_course, width="stretch", hide_index=True)
        with right:
            section_label("Season Leaders")
            st.subheader("Fastest visible runner by year")
            st.dataframe(fastest_year, width="stretch", hide_index=True)

    with runner_tab:
        st.caption("Runner Lab searches the full dataset. The sidebar lens still shapes the other tabs.")
        runner_search = st.text_input(
            "Find runner by name",
            placeholder="Try: ADHNI",
            key="runner-search-query",
        )
        options = runner_search_options(df, runner_search, limit=80)
        if not options:
            st.warning("No runners match that search. Try a broader partial name.")
        else:
            runner_labels = runner_option_labels(df)
            runner_name = st.selectbox(
                "Matching runners",
                options,
                index=0,
                format_func=lambda name: runner_labels.get(name, name),
            )
            runner_roadmap = road_to_stars(df, marathons)
            runner_stats = runner_summary(df, runner_name)
            runner_df = runner_results(df, runner_name)
            runner_best = runner_best_by_marathon(df, runner_name)
            runner_progress = runner_progression(df, runner_name)
            runner_breakdown = runner_marathon_breakdown(df, runner_name)
            runner_road = runner_roadmap.loc[runner_roadmap["Name"] == runner_name].iloc[0]
            runner_milestone_table = runner_milestones(df, runner_name, marathons)
            runner_story = runner_personal_story(df, runner_name, marathons)
            runner_rarity = runner_rarity_summary(df, runner_name)
            runner_goals = runner_next_goals(df, runner_name, marathons)
            runner_badge_list = runner_badges(df, runner_name, marathons)
            review_year_options = sorted(runner_df["Year"].unique(), reverse=True)
            runner_slug = runner_name.lower().replace(" ", "_")
            passport_png = runner_passport_card(runner_name, runner_stats, runner_road, runner_story)
            journey_png = runner_milestones_card(runner_name, runner_milestone_table, runner_badge_list)
            goals_png = runner_goals_card(runner_name, runner_goals, runner_rarity)

            st.markdown(f"## {runner_name}")
            current_lens_rows = int((filtered["Name"] == runner_name).sum())
            if current_lens_rows:
                st.caption(
                    f"A personal achievement view from the full dataset. {current_lens_rows} finish"
                    f"{'es' if current_lens_rows != 1 else ''} for this runner also sit inside the current dashboard lens."
                )
            else:
                st.caption("A personal achievement view from the full dataset. This runner sits outside the current dashboard lens.")

            render_passport_card(runner_name, runner_stats, runner_road, runner_story)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Entries", runner_stats["entries"])
            c2.metric("Stars", runner_stats["stars"])
            c3.metric("Years Active", runner_stats["years_active"])
            c4.metric("Best Time", runner_stats["best_time"])
            c5.metric("Best Indo Rank", f"#{runner_stats['best_indo_place']}")

            section_label("How Rare")
            st.subheader("Where this runner stands in the field")
            rarity_columns = st.columns(len(runner_rarity))
            for idx, row in runner_rarity.iterrows():
                with rarity_columns[idx]:
                    st.metric(str(row["Metric"]), str(row["Standing"]))
                    st.caption(f"{row['Rank']} • value {row['Value']}")

            section_label("Badge Cabinet")
            st.subheader("Unlocked achievements")
            badge_columns = st.columns(4)
            for idx, badge in enumerate(runner_badge_list):
                with badge_columns[idx % 4]:
                    render_personal_badge(str(badge["title"]), str(badge["detail"]))

            section_label("What's Next")
            st.subheader("Practical next steps for this runner")
            goal_columns = st.columns(len(runner_goals))
            for idx, (_, goal_row) in enumerate(runner_goals.iterrows()):
                with goal_columns[idx]:
                    render_goal_card(
                        str(goal_row["Goal"]),
                        str(goal_row["Target"]),
                        str(goal_row["Gap"]),
                        str(goal_row["Why"]),
                    )

            section_label("Year In Review")
            selected_review_year = st.selectbox(
                "Season to review",
                review_year_options,
                index=0,
                key=f"review-year-{runner_name}",
            )
            runner_review = runner_year_in_review(df, runner_name, int(selected_review_year), marathons)
            season_results = (
                runner_df.loc[runner_df["Year"] == selected_review_year, ["Marathon", "Time", "Indo_Place", "Place"]]
                .reset_index(drop=True)
            )
            review_png = runner_year_review_card(runner_name, runner_review)
            st.subheader(f"{selected_review_year} season snapshot")
            render_story_card(str(runner_review["Story"]))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Visible Finishes", int(runner_review["Finishes"]))
            c2.metric("New Stars", int(runner_review["New_Stars"]))
            c3.metric("Season Best", str(runner_review["Best_Time"]))
            c4.metric("Best Indo Rank", f"#{runner_review['Best_Indo_Place']}")

            left, right = st.columns([1.2, 1])
            with left:
                st.caption("Visible results in the selected season")
                st.dataframe(season_results, width="stretch", hide_index=True)
            with right:
                st.caption("Season highlights")
                for highlight in list(runner_review["Highlights"]):
                    st.markdown(f"- {highlight}")

            section_label("Share Cards")
            st.subheader("Download achievement cards for this runner")
            card_tab_1, card_tab_2, card_tab_3, card_tab_4 = st.tabs(
                ["Passport Card", "Journey Card", "Next Goals Card", "Year In Review"]
            )

            with card_tab_1:
                st.image(passport_png, width="stretch")
                st.download_button(
                    "Download Passport Card",
                    data=passport_png,
                    file_name=f"{runner_slug}_passport_card.png",
                    mime="image/png",
                )

            with card_tab_2:
                st.image(journey_png, width="stretch")
                st.download_button(
                    "Download Journey Card",
                    data=journey_png,
                    file_name=f"{runner_slug}_journey_card.png",
                    mime="image/png",
                )

            with card_tab_3:
                st.image(goals_png, width="stretch")
                st.download_button(
                    "Download Next Goals Card",
                    data=goals_png,
                    file_name=f"{runner_slug}_next_goals_card.png",
                    mime="image/png",
                )

            with card_tab_4:
                st.image(review_png, width="stretch")
                st.download_button(
                    f"Download {selected_review_year} Year In Review Card",
                    data=review_png,
                    file_name=f"{runner_slug}_{selected_review_year}_year_in_review_card.png",
                    mime="image/png",
                )

            left, right = st.columns(2)
            with left:
                section_label("Progression")
                st.subheader("Best result by year")
                st.altair_chart(runner_progression_chart(runner_progress), use_container_width=True)
            with right:
                section_label("Course Mix")
                st.subheader("Where this runner keeps showing up")
                st.altair_chart(runner_breakdown_chart(runner_breakdown), use_container_width=True)

            left, right = st.columns([0.95, 1.05])
            with left:
                section_label("Rank")
                st.subheader("Indonesian placing by race")
                st.altair_chart(runner_rank_chart(runner_df), use_container_width=True)
            with right:
                section_label("Milestones")
                st.subheader("Journey moments")
                st.dataframe(runner_milestone_table, width="stretch", hide_index=True)

            left, right = st.columns([0.95, 1.05])
            with left:
                section_label("Best Splits")
                st.subheader("Best result by marathon")
                st.dataframe(runner_best, width="stretch", hide_index=True)
            with right:
                section_label("Career Log")
                st.subheader("All visible results")
                st.dataframe(runner_df, width="stretch", hide_index=True)
                st.download_button(
                    "Download Runner Log",
                    data=to_csv_bytes(runner_df),
                    file_name=f"{runner_slug}_results.csv",
                    mime="text/csv",
                )

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
            st.dataframe(stars, width="stretch", hide_index=True)
        with right:
            section_label("Raw View")
            st.subheader("Filtered raw data")
            st.dataframe(filtered, width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
