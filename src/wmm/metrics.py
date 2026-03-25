from __future__ import annotations

import pandas as pd

from .data import format_seconds_to_hm, format_seconds_to_hms


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
