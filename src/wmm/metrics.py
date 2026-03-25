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
    return {
        "rows": len(df),
        "runners": int(df["Name"].nunique()),
        "marathons": int(df["Marathon"].nunique()),
        "year_range": f"{int(df['Year'].min())}-{int(df['Year'].max())}",
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
