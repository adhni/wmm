"""Coverage is explicit: an absent result row never implies zero finishers."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .catalog import RACES, TARGET_YEAR
from .data import ROOT_DIR

COVERAGE_PATH = ROOT_DIR / "data" / "coverage.json"
STATUSES = {"complete", "partial", "unavailable", "verified zero finishers", "event not held"}


def initial_coverage(legacy: pd.DataFrame) -> list[dict]:
    counts = legacy.groupby(["Marathon", "Year"]).size().to_dict()
    rows = []
    for marathon, race in RACES.items():
        for year in range(race["start_year"], TARGET_YEAR + 1):
            count = int(counts.get((marathon, year), 0))
            rows.append({
                "Marathon": marathon, "Year": year, "Edition_Year": year,
                "Status": "partial" if count else "unavailable",
                "Imported_Count": count, "Expected_Count": None,
                "Source_URL": race["source"], "Retrieved_At": None,
                "Note": "Legacy results; completeness not audited." if count else "Results not imported; not a confirmed zero.",
            })
            if marathon == "Tokyo" and year == 2021:
                rows[-1].update(Status="event not held", Note="The 2021 edition was postponed to 2022-03-06; results belong to calendar year 2022.")
    return rows


def load_coverage(path: Path = COVERAGE_PATH) -> pd.DataFrame:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return pd.DataFrame(rows)


def comparable_years(coverage: pd.DataFrame, marathons: list[str], year: int) -> bool:
    """Only compare complete cohorts of the same races in consecutive years."""
    for previous_year in (year - 1, year):
        subset = coverage.loc[
            coverage["Marathon"].isin(marathons) & coverage["Year"].eq(previous_year)
        ]
        if set(subset["Marathon"]) != set(marathons):
            return False
        if not subset["Status"].isin(["complete", "verified zero finishers"]).all():
            return False
    return True
