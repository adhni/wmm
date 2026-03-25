from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "raw_data.csv"


def format_seconds_to_hms(seconds: int | float) -> str:
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_remainder = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds_remainder:02d}"


def format_seconds_to_hm(seconds: int | float) -> str:
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours:02d}:{minutes:02d}"


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Name"] = df["Name"].str.upper().str.strip()
    df["Year"] = df["Year"].astype(int)
    df["Place"] = df["Place"].astype(int)
    df["Time_seconds"] = pd.to_timedelta(df["Time"]).dt.total_seconds().astype(int)
    df["Time_HHMM"] = df["Time_seconds"].map(format_seconds_to_hm)
    return df.sort_values(["Year", "Marathon", "Time_seconds", "Name"]).reset_index(drop=True)
