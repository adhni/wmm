from __future__ import annotations

from pathlib import Path
import hashlib
import json

import pandas as pd

from .catalog import RACES


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "raw_data.csv"
REQUIRED_COLUMNS = ["Marathon", "Year", "Name", "Time", "Place"]
EXPECTED_MARATHONS = set(RACES)


def format_place(value: object) -> str:
    return "—" if pd.isna(value) else str(int(value))


def record_key(row: dict) -> str:
    values = ["" if pd.isna(row.get(c)) else str(row.get(c, "")) for c in REQUIRED_COLUMNS]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


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


def format_seconds_delta(seconds: int | float) -> str:
    total_seconds = abs(int(round(seconds)))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_remainder = total_seconds % 60
    if hours:
        return f"{hours}h {minutes:02d}m {seconds_remainder:02d}s"
    return f"{minutes}m {seconds_remainder:02d}s"


def _validate_required_columns(df: pd.DataFrame) -> None:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing}")


def _validate_non_blank(df: pd.DataFrame, column: str) -> None:
    values = df[column]
    invalid = values.isna() | values.astype(str).str.strip().eq("")
    if invalid.any():
        raise ValueError(f"Column {column} contains blank values")


def _validate_marathons(df: pd.DataFrame) -> None:
    marathons = df["Marathon"].astype(str).str.strip()
    unexpected = sorted(set(marathons) - EXPECTED_MARATHONS)
    if unexpected:
        values = ", ".join(unexpected)
        raise ValueError(f"Unexpected marathon values: {values}")


def _parse_int_column(df: pd.DataFrame, column: str) -> pd.Series:
    parsed = pd.to_numeric(df[column], errors="coerce")
    invalid = parsed.isna() | (parsed % 1 != 0)
    if invalid.any():
        raise ValueError(f"Column {column} must contain whole numbers")
    return parsed.astype(int)


def _parse_time_column(df: pd.DataFrame) -> pd.Series:
    if not df["Time"].astype(str).str.fullmatch(r"\d+:[0-5]\d:[0-5]\d").all():
        raise ValueError("Column Time contains invalid duration values")
    parsed = pd.to_timedelta(df["Time"], errors="coerce")
    if parsed.isna().any() or (parsed <= pd.Timedelta(0)).any():
        raise ValueError("Column Time contains invalid duration values")
    return parsed.dt.total_seconds().astype(int)


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    _validate_required_columns(df)
    for column in REQUIRED_COLUMNS:
        if column != "Place":
            _validate_non_blank(df, column)
    _validate_marathons(df)

    df["Name"] = df["Name"].str.upper().str.strip()
    df["Marathon"] = df["Marathon"].str.strip()
    df["Year"] = _parse_int_column(df, "Year")
    places = pd.to_numeric(df["Place"], errors="coerce")
    supplied = df["Place"].notna() & df["Place"].astype(str).str.strip().ne("")
    if (supplied & (places.isna() | (places % 1 != 0) | (places <= 0))).any():
        raise ValueError("Column Place must contain positive whole numbers or blanks")
    df["Place"] = places.astype("Int64")
    metadata_path = ROOT_DIR / "data" / "result_metadata.csv"
    if Path(path).resolve() == DATA_PATH.resolve() and metadata_path.exists():
        metadata = pd.read_csv(metadata_path, dtype=str)
        df["Record_Key"] = df.apply(lambda row: record_key(row.to_dict()), axis=1)
        df = df.merge(metadata, on="Record_Key", how="left", validate="many_to_one")
        df = df.drop(columns="Record_Key")
    df["Time_seconds"] = _parse_time_column(df)
    df["Time_HHMM"] = df["Time_seconds"].map(format_seconds_to_hm)
    df = df.sort_values(["Year", "Marathon", "Time_seconds", "Name"]).reset_index(drop=True)
    df["Indo_Place"] = (
        df.groupby(["Year", "Marathon"])["Time_seconds"]
        .rank(method="dense", ascending=True)
        .astype(int)
    )
    return df
