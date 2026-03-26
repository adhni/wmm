from __future__ import annotations

import pandas as pd

from .data import format_seconds_delta, format_seconds_to_hm, format_seconds_to_hms


def filtered_data(
    df: pd.DataFrame,
    selected_marathons: list[str],
    year_min: int,
    year_max: int,
) -> pd.DataFrame:
    mask = (
        df["Marathon"].isin(selected_marathons)
        & df["Year"].between(year_min, year_max)
    )
    return df.loc[mask].copy()


def summary_metrics(df: pd.DataFrame) -> dict[str, str | int]:
    fastest = df.nsmallest(1, "Time_seconds").iloc[0]
    latest_year = int(df["Year"].max())
    latest_year_df = df.loc[df["Year"] == latest_year]
    previous_year_df = df.loc[df["Year"] == latest_year - 1]
    latest_entries = len(latest_year_df)
    previous_entries = len(previous_year_df)
    return {
        "rows": len(df),
        "runners": int(df["Name"].nunique()),
        "marathons": int(df["Marathon"].nunique()),
        "year_range": f"{int(df['Year'].min())}-{int(df['Year'].max())}",
        "latest_year": latest_year,
        "latest_entries": latest_entries,
        "entry_delta": latest_entries - previous_entries if previous_entries else latest_entries,
        "fastest_label": (
            f"{fastest['Name']} | {fastest['Marathon']} {int(fastest['Year'])} | "
            f"{fastest['Time']}"
        ),
    }


def runner_growth(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["Year", "Marathon"], as_index=False)
        .size()
        .rename(columns={"size": "Runner_Count"})
        .sort_values(["Year", "Marathon"])
    )


def median_finish_times(df: pd.DataFrame) -> pd.DataFrame:
    median_df = (
        df.groupby(["Year", "Marathon"], as_index=False)["Time_seconds"]
        .median()
        .rename(columns={"Time_seconds": "Median_Time_Seconds"})
    )
    median_df["Median_Time_HHMM"] = median_df["Median_Time_Seconds"].map(format_seconds_to_hm)
    return median_df.sort_values(["Year", "Marathon"])


def fastest_by_marathon(df: pd.DataFrame) -> pd.DataFrame:
    fastest = (
        df.sort_values("Time_seconds")
        .groupby("Marathon", as_index=False)
        .first()[["Marathon", "Year", "Name", "Time", "Place"]]
        .sort_values(["Time", "Marathon"])
    )
    return fastest


def fastest_by_year(df: pd.DataFrame) -> pd.DataFrame:
    fastest = (
        df.sort_values("Time_seconds")
        .groupby("Year", as_index=False)
        .first()[["Year", "Marathon", "Name", "Time", "Place"]]
        .sort_values("Year")
    )
    return fastest


def top_repeat_runners(df: pd.DataFrame, limit: int = 15) -> pd.DataFrame:
    counts = (
        df.groupby("Name", as_index=False)
        .agg(
            Entries=("Name", "size"),
            Unique_Marathons=("Marathon", "nunique"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values(["Entries", "Unique_Marathons", "Best_Time_Seconds", "Name"], ascending=[False, False, True, True])
        .head(limit)
    )
    counts["Best_Time"] = counts["Best_Time_Seconds"].map(format_seconds_to_hms)
    return counts[["Name", "Entries", "Unique_Marathons", "Best_Time"]]


def star_table(df: pd.DataFrame) -> pd.DataFrame:
    participation = (
        df.groupby(["Name", "Marathon"], as_index=False)
        .agg(Years=("Year", lambda s: ", ".join(str(y) for y in sorted(set(s)))))
    )

    stars = participation.pivot(index="Name", columns="Marathon", values="Years").fillna("")
    stars = stars.reset_index()
    marathon_columns = [col for col in stars.columns if col != "Name"]
    stars["Stars"] = (stars[marathon_columns] != "").sum(axis=1)

    pb = (
        df.groupby("Name", as_index=False)["Time_seconds"]
        .min()
        .rename(columns={"Time_seconds": "WMM_PB_Seconds"})
    )
    pb["WMM_PB"] = pb["WMM_PB_Seconds"].map(format_seconds_to_hms)

    result = stars.merge(pb[["Name", "WMM_PB"]], on="Name", how="left")
    ordered_columns = ["Name", "Stars", "WMM_PB"] + sorted(marathon_columns)
    return result[ordered_columns].sort_values(["Stars", "Name"], ascending=[False, True])


def yearly_leaders(df: pd.DataFrame) -> pd.DataFrame:
    leaders = (
        df.sort_values("Time_seconds")
        .groupby(["Year", "Marathon"], as_index=False)
        .first()[["Year", "Marathon", "Name", "Time", "Place"]]
        .sort_values(["Year", "Time"])
    )
    return leaders


def latest_year_snapshot(df: pd.DataFrame) -> tuple[int, pd.DataFrame]:
    latest_year = int(df["Year"].max())
    snapshot = (
        df.loc[df["Year"] == latest_year]
        .groupby("Marathon", as_index=False)
        .agg(
            Runner_Count=("Marathon", "size"),
            Unique_Runners=("Name", "nunique"),
            Median_Time_Seconds=("Time_seconds", "median"),
            Fastest_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values("Runner_Count", ascending=False)
        .reset_index(drop=True)
    )
    snapshot["Median_Time"] = snapshot["Median_Time_Seconds"].map(format_seconds_to_hm)
    snapshot["Fastest_Time"] = snapshot["Fastest_Time_Seconds"].map(format_seconds_to_hms)
    return latest_year, snapshot


def marathon_rankings(df: pd.DataFrame) -> pd.DataFrame:
    rankings = runner_growth(df)
    rankings["Rank"] = rankings.groupby("Year")["Runner_Count"].rank(
        method="dense", ascending=False
    )
    rankings["Rank"] = rankings["Rank"].astype(int)
    return rankings.sort_values(["Year", "Rank", "Marathon"]).reset_index(drop=True)


def finish_time_spectrum(df: pd.DataFrame, bin_minutes: int = 15) -> pd.DataFrame:
    min_seconds = 2 * 3600 + 30 * 60
    max_seconds = 8 * 3600
    step = bin_minutes * 60
    bins = list(range(min_seconds, max_seconds + step, step))
    labels = [
        f"{format_seconds_to_hm(left)}-{format_seconds_to_hm(right)}"
        for left, right in zip(bins[:-1], bins[1:])
    ]
    spectrum = df.copy()
    spectrum["Time_Bin"] = pd.cut(
        spectrum["Time_seconds"],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )
    spectrum = spectrum.dropna(subset=["Time_Bin"])
    spectrum = (
        spectrum.groupby(["Marathon", "Time_Bin"], as_index=False, observed=True)
        .size()
        .rename(columns={"size": "Runner_Count"})
    )
    spectrum["Time_Bin"] = spectrum["Time_Bin"].astype(str)
    return spectrum


def star_distribution(df: pd.DataFrame) -> pd.DataFrame:
    stars = (
        df.groupby("Name", as_index=False)
        .agg(Stars=("Marathon", "nunique"))
        .groupby("Stars", as_index=False)
        .size()
        .rename(columns={"size": "Runner_Count"})
        .sort_values("Stars")
    )
    return stars


def road_to_stars(df: pd.DataFrame, marathon_universe: list[str]) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    universe = list(marathon_universe)

    for name, group in df.groupby("Name"):
        completed_set = set(group["Marathon"].unique())
        completed = [marathon for marathon in universe if marathon in completed_set]
        missing = [marathon for marathon in universe if marathon not in completed_set]
        stars = len(completed)
        if stars == len(universe):
            status = "Complete"
        elif stars == len(universe) - 1:
            status = "One away"
        elif stars >= max(len(universe) - 2, 1):
            status = "In striking distance"
        else:
            status = "Building"

        rows.append(
            {
                "Name": name,
                "Stars": stars,
                "Entries": len(group),
                "Latest_Year": int(group["Year"].max()),
                "WMM_PB_Seconds": int(group["Time_seconds"].min()),
                "WMM_PB": format_seconds_to_hms(group["Time_seconds"].min()),
                "Completed_Majors": ", ".join(completed),
                "Missing_Majors": ", ".join(missing) if missing else "None",
                "Missing_Count": len(missing),
                "Status": status,
            }
        )

    result = pd.DataFrame(rows).sort_values(
        ["Stars", "Missing_Count", "Entries", "Latest_Year", "WMM_PB_Seconds", "Name"],
        ascending=[False, True, False, False, True, True],
    )
    return result.reset_index(drop=True)


def star_status_summary(road_df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        road_df.groupby("Status", as_index=False)
        .size()
        .rename(columns={"size": "Runner_Count"})
    )
    status_order = ["Complete", "One away", "In striking distance", "Building"]
    summary["Order"] = summary["Status"].map({label: idx for idx, label in enumerate(status_order)})
    summary = summary.sort_values("Order").drop(columns="Order").reset_index(drop=True)
    return summary


def missing_major_pressure(road_df: pd.DataFrame) -> pd.DataFrame:
    base = road_df.loc[road_df["Status"] == "One away", ["Name", "Missing_Majors"]].copy()
    if base.empty:
        return pd.DataFrame(columns=["Marathon", "Runner_Count"])
    pressure = (
        base.assign(Marathon=base["Missing_Majors"].str.split(", "))
        .explode("Marathon")
        .groupby("Marathon", as_index=False)
        .size()
        .rename(columns={"size": "Runner_Count"})
        .sort_values(["Runner_Count", "Marathon"], ascending=[False, True])
        .reset_index(drop=True)
    )
    return pressure


def entry_leaderboard(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    leaderboard = (
        df.groupby("Name", as_index=False)
        .agg(
            Entries=("Name", "size"),
            Stars=("Marathon", "nunique"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values(["Entries", "Stars", "Best_Time_Seconds", "Name"], ascending=[False, False, True, True])
        .head(limit)
        .reset_index(drop=True)
    )
    leaderboard["Best_Time"] = leaderboard["Best_Time_Seconds"].map(format_seconds_to_hms)
    return leaderboard[["Name", "Entries", "Stars", "Best_Time"]]


def star_leaderboard(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    leaderboard = (
        df.groupby("Name", as_index=False)
        .agg(
            Stars=("Marathon", "nunique"),
            Entries=("Name", "size"),
            Latest_Year=("Year", "max"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values(["Stars", "Entries", "Latest_Year", "Best_Time_Seconds", "Name"], ascending=[False, False, False, True, True])
        .head(limit)
        .reset_index(drop=True)
    )
    leaderboard["Best_Time"] = leaderboard["Best_Time_Seconds"].map(format_seconds_to_hms)
    return leaderboard[["Name", "Stars", "Entries", "Latest_Year", "Best_Time"]]


def active_years_leaderboard(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    leaderboard = (
        df.groupby("Name", as_index=False)
        .agg(
            Active_Years=("Year", "nunique"),
            Entries=("Name", "size"),
            Stars=("Marathon", "nunique"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values(["Active_Years", "Entries", "Stars", "Best_Time_Seconds", "Name"], ascending=[False, False, False, True, True])
        .head(limit)
        .reset_index(drop=True)
    )
    leaderboard["Best_Time"] = leaderboard["Best_Time_Seconds"].map(format_seconds_to_hms)
    return leaderboard[["Name", "Active_Years", "Entries", "Stars", "Best_Time"]]


def sub4_leaderboard(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    leaderboard = (
        df.assign(Sub4=(df["Time_seconds"] < 4 * 3600).astype(int))
        .groupby("Name", as_index=False)
        .agg(
            Sub4_Finishes=("Sub4", "sum"),
            Entries=("Name", "size"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .query("Sub4_Finishes > 0")
        .sort_values(["Sub4_Finishes", "Entries", "Best_Time_Seconds", "Name"], ascending=[False, False, True, True])
        .head(limit)
        .reset_index(drop=True)
    )
    leaderboard["Best_Time"] = leaderboard["Best_Time_Seconds"].map(format_seconds_to_hms)
    return leaderboard[["Name", "Sub4_Finishes", "Entries", "Best_Time"]]


def improvement_leaderboard(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    rows: list[dict[str, str | int]] = []
    for name, group in df.groupby("Name"):
        if len(group) < 2:
            continue
        first_year = int(group["Year"].min())
        first_year_best = int(group.loc[group["Year"] == first_year, "Time_seconds"].min())
        best_time = int(group["Time_seconds"].min())
        improvement = first_year_best - best_time
        if improvement <= 0:
            continue
        rows.append(
            {
                "Name": name,
                "First_Year": first_year,
                "First_Year_Best": format_seconds_to_hms(first_year_best),
                "Current_Best": format_seconds_to_hms(best_time),
                "Improvement_Seconds": improvement,
                "Improvement": format_seconds_delta(improvement),
            }
        )
    leaderboard = pd.DataFrame(rows)
    if leaderboard.empty:
        return pd.DataFrame(columns=["Name", "First_Year", "First_Year_Best", "Current_Best", "Improvement"])
    leaderboard = leaderboard.sort_values(["Improvement_Seconds", "Name"], ascending=[False, True]).head(limit)
    return leaderboard[["Name", "First_Year", "First_Year_Best", "Current_Best", "Improvement"]].reset_index(drop=True)


def hall_of_fame_cards(df: pd.DataFrame) -> list[dict[str, str]]:
    entries = entry_leaderboard(df, 1).iloc[0]
    stars = star_leaderboard(df, 1).iloc[0]
    fastest = df.nsmallest(1, "Time_seconds").iloc[0]
    active = active_years_leaderboard(df, 1).iloc[0]
    cards = [
        {
            "title": "Most Entries",
            "winner": str(entries["Name"]),
            "detail": f"{int(entries['Entries'])} visible finishes",
        },
        {
            "title": "Most Stars",
            "winner": str(stars["Name"]),
            "detail": f"{int(stars['Stars'])} majors across {int(stars['Entries'])} finishes",
        },
        {
            "title": "Fastest Overall",
            "winner": str(fastest["Name"]),
            "detail": f"{fastest['Marathon']} {int(fastest['Year'])} • {fastest['Time']}",
        },
        {
            "title": "Longest Visible Career",
            "winner": str(active["Name"]),
            "detail": f"{int(active['Active_Years'])} active years",
        },
    ]
    sub4 = sub4_leaderboard(df, 1)
    if not sub4.empty:
        leader = sub4.iloc[0]
        cards.append(
            {
                "title": "Sub-4 Machine",
                "winner": str(leader["Name"]),
                "detail": f"{int(leader['Sub4_Finishes'])} sub-4 finishes",
            }
        )
    improvement = improvement_leaderboard(df, 1)
    if not improvement.empty:
        leader = improvement.iloc[0]
        cards.append(
            {
                "title": "Biggest Improvement",
                "winner": str(leader["Name"]),
                "detail": f"{leader['Improvement']} faster than first visible year",
            }
        )
    return cards


def marathon_profile_summary(df: pd.DataFrame, marathon: str) -> dict[str, str | int | float]:
    marathon_df = df.loc[df["Marathon"] == marathon].copy()
    per_runner = marathon_df.groupby("Name", as_index=False).agg(Entries=("Marathon", "size"))
    all_runner_stars = df.groupby("Name", as_index=False).agg(Stars=("Marathon", "nunique"))
    merged = per_runner.merge(all_runner_stars, on="Name", how="left")
    repeat_share = (merged["Entries"] > 1).mean() if not merged.empty else 0
    multi_star_share = (merged["Stars"] >= 3).mean() if not merged.empty else 0
    fastest = marathon_df.nsmallest(1, "Time_seconds").iloc[0]
    latest_year = int(marathon_df["Year"].max())
    latest_count = int((marathon_df["Year"] == latest_year).sum())
    return {
        "entries": len(marathon_df),
        "unique_runners": int(marathon_df["Name"].nunique()),
        "latest_year": latest_year,
        "latest_count": latest_count,
        "median_time": format_seconds_to_hm(marathon_df["Time_seconds"].median()),
        "fastest_time": str(fastest["Time"]),
        "fastest_runner": str(fastest["Name"]),
        "repeat_share": float(round(repeat_share * 100, 1)),
        "multi_star_share": float(round(multi_star_share * 100, 1)),
    }


def marathon_top_performers(df: pd.DataFrame, marathon: str, limit: int = 12) -> pd.DataFrame:
    top = (
        df.loc[df["Marathon"] == marathon, ["Year", "Name", "Time", "Indo_Place", "Place", "Time_seconds"]]
        .sort_values(["Time_seconds", "Year", "Name"])
        .head(limit)
        .reset_index(drop=True)
    )
    return top.drop(columns=["Time_seconds"])


def runner_milestones(df: pd.DataFrame, runner_name: str, marathon_universe: list[str]) -> pd.DataFrame:
    runner_df = (
        df.loc[df["Name"] == runner_name]
        .sort_values(["Year", "Time_seconds", "Marathon"])
        .reset_index(drop=True)
    )
    milestones: list[dict[str, str | int]] = []

    first = runner_df.iloc[0]
    milestones.append(
        {
            "Order": 1,
            "Milestone": "First visible major",
            "Year": int(first["Year"]),
            "Detail": f"{first['Marathon']} • {first['Time']}",
        }
    )

    thresholds = [
        ("First sub-5", 5 * 3600),
        ("First sub-4:30", 4 * 3600 + 30 * 60),
        ("First sub-4", 4 * 3600),
        ("First sub-3:30", 3 * 3600 + 30 * 60),
    ]
    order = 10
    for label, seconds in thresholds:
        hits = runner_df.loc[runner_df["Time_seconds"] < seconds]
        if not hits.empty:
            hit = hits.iloc[0]
            milestones.append(
                {
                    "Order": order,
                    "Milestone": label,
                    "Year": int(hit["Year"]),
                    "Detail": f"{hit['Marathon']} • {hit['Time']}",
                }
            )
        order += 1

    seen: set[str] = set()
    reached: set[int] = set()
    for year in sorted(runner_df["Year"].unique()):
        seen.update(runner_df.loc[runner_df["Year"] == year, "Marathon"].unique())
        for threshold in range(2, len(marathon_universe) + 1):
            if len(seen) >= threshold and threshold not in reached:
                milestones.append(
                    {
                        "Order": 30 + threshold,
                        "Milestone": f"Reached {threshold} stars",
                        "Year": int(year),
                        "Detail": ", ".join(m for m in marathon_universe if m in seen),
                    }
                )
                reached.add(threshold)

    best = runner_df.nsmallest(1, "Time_seconds").iloc[0]
    milestones.append(
        {
            "Order": 99,
            "Milestone": "Best visible result",
            "Year": int(best["Year"]),
            "Detail": f"{best['Marathon']} • {best['Time']} • indo #{int(best['Indo_Place'])}",
        }
    )

    result = (
        pd.DataFrame(milestones)
        .sort_values(["Order", "Year", "Milestone"])
        .drop(columns="Order")
        .reset_index(drop=True)
    )
    return result


def runner_options(df: pd.DataFrame) -> list[str]:
    counts = (
        df.groupby("Name", as_index=False)
        .agg(
            Entries=("Name", "size"),
            Stars=("Marathon", "nunique"),
            Best_Time_Seconds=("Time_seconds", "min"),
        )
        .sort_values(
            ["Entries", "Stars", "Best_Time_Seconds", "Name"],
            ascending=[False, False, True, True],
        )
    )
    counts["Label"] = counts.apply(
        lambda row: f"{row['Name']} ({int(row['Entries'])} entries, {int(row['Stars'])} stars)",
        axis=1,
    )
    return counts["Label"].tolist()


def runner_name_from_option(option: str) -> str:
    return option.rsplit(" (", 1)[0]


def runner_summary(df: pd.DataFrame, runner_name: str) -> dict[str, str | int]:
    runner_df = df.loc[df["Name"] == runner_name].copy()
    best = runner_df.nsmallest(1, "Time_seconds").iloc[0]
    latest = runner_df.sort_values(["Year", "Time_seconds"]).iloc[-1]
    return {
        "entries": len(runner_df),
        "stars": int(runner_df["Marathon"].nunique()),
        "years_active": int(runner_df["Year"].nunique()),
        "best_time": str(best["Time"]),
        "best_result": (
            f"{best['Marathon']} {int(best['Year'])} | "
            f"indo #{int(best['Indo_Place'])} | place {int(best['Place'])}"
        ),
        "latest_result": (
            f"{latest['Marathon']} {int(latest['Year'])} | "
            f"{latest['Time']} | indo #{int(latest['Indo_Place'])}"
        ),
    }


def runner_results(df: pd.DataFrame, runner_name: str) -> pd.DataFrame:
    runner_df = (
        df.loc[
            df["Name"] == runner_name,
            ["Year", "Marathon", "Time", "Indo_Place", "Place", "Time_seconds"],
        ]
        .sort_values(["Year", "Marathon", "Time_seconds"])
        .reset_index(drop=True)
    )
    return runner_df.drop(columns=["Time_seconds"])


def runner_best_by_marathon(df: pd.DataFrame, runner_name: str) -> pd.DataFrame:
    runner_df = df.loc[df["Name"] == runner_name].copy()
    best = (
        runner_df.sort_values("Time_seconds")
        .groupby("Marathon", as_index=False)
        .first()[["Marathon", "Year", "Time", "Indo_Place", "Place"]]
        .sort_values(["Time", "Marathon"])
        .reset_index(drop=True)
    )
    return best


def runner_progression(df: pd.DataFrame, runner_name: str) -> pd.DataFrame:
    runner_df = df.loc[df["Name"] == runner_name].copy()
    progression = (
        runner_df.sort_values("Time_seconds")
        .groupby("Year", as_index=False)
        .first()[["Year", "Marathon", "Time_seconds", "Time", "Indo_Place"]]
        .sort_values("Year")
        .reset_index(drop=True)
    )
    progression["Time_HHMM"] = progression["Time_seconds"].map(format_seconds_to_hm)
    return progression


def runner_marathon_breakdown(df: pd.DataFrame, runner_name: str) -> pd.DataFrame:
    runner_df = df.loc[df["Name"] == runner_name].copy()
    breakdown = (
        runner_df.groupby("Marathon", as_index=False)
        .agg(
            Entries=("Marathon", "size"),
            Best_Time_Seconds=("Time_seconds", "min"),
            First_Year=("Year", "min"),
            Latest_Year=("Year", "max"),
        )
        .sort_values(["Entries", "Best_Time_Seconds", "Marathon"], ascending=[False, True, True])
        .reset_index(drop=True)
    )
    breakdown["Best_Time"] = breakdown["Best_Time_Seconds"].map(format_seconds_to_hms)
    return breakdown[["Marathon", "Entries", "Best_Time", "First_Year", "Latest_Year"]]


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
