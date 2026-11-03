"""Maintainer CLI for source exports, edition imports, and reproducible builds.

Network access is confined to collection and ``fetch``; Streamlit never fetches race results.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
import shutil
import tempfile
import urllib.request

import pandas as pd

from .catalog import RACES, TARGET_YEAR
from .coverage import STATUSES, initial_coverage
from .data import REQUIRED_COLUMNS, ROOT_DIR, format_seconds_to_hms, load_data, record_key

INDONESIA = {"ID", "IDN", "INA", "INDONESIA"}
METADATA_COLUMNS = ["Record_Key", "Source_Result_ID", "Source_URL", "Race_Date", "Edition_Year", "Country_Field", "Country_Value", "Time_Basis", "Place_Basis"]


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        temporary = Path(tmp.name)
        tmp.write(content)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _csv(rows: list[dict], columns: list[str]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Source must have unique CSV column headers")
        rows = list(reader)
    if any(None in r or any(value is None for value in r.values()) for r in rows):
        raise ValueError("Source contains malformed CSV rows")
    return rows


def import_edition(source: Path, config: dict, data_dir: Path = ROOT_DIR / "data") -> dict:
    """Validate first, then replace one imported edition and retain its source."""
    marathon = config["marathon"]
    if marathon not in RACES:
        raise ValueError("Unknown marathon")
    race_date = date.fromisoformat(config["race_date"])
    edition = int(config["edition_year"])
    if not RACES[marathon]["start_year"] <= race_date.year <= TARGET_YEAR:
        raise ValueError("Race date is outside this project's coverage")
    if not RACES[marathon]["start_year"] <= edition <= TARGET_YEAR:
        raise ValueError("Edition is outside this project's coverage")
    if marathon == "Tokyo" and edition == 2021 and race_date != date(2022, 3, 6):
        raise ValueError("Tokyo's 2021 edition was held on 2022-03-06")
    if marathon == "Tokyo" and edition == 2022:
        raise ValueError("Tokyo had no separate 2022 edition; import the 2021 edition held on 2022-03-06")
    if edition != race_date.year and not (marathon == "Tokyo" and edition == 2021):
        raise ValueError("Edition year and race date year differ without a supported postponement")
    if not config.get("source_url", "").startswith(("https://", "http://")):
        raise ValueError("A public source URL is required")
    if config.get("country_field_type") not in {"nationality", "citizenship", "country", "residence"}:
        raise ValueError("Declare the meaning of the source country field")
    if config.get("time_basis") not in {"net", "gun", "official"}:
        raise ValueError("Declare net, gun, or official time_basis")
    if config.get("place_basis") not in {"overall", "gender", "category", "unknown"}:
        raise ValueError("Declare the source place_basis")
    mapping = config["columns"]
    if not all(field in mapping for field in ("name", "country", "time")):
        raise ValueError("Map name, country, and time columns")
    for flag, field in (("finishers_only", "status"), ("marathon_only", "distance"), ("running_only", "division")):
        if config.get(flag) is not True and (field not in mapping or not config.get(field + "_values")):
            raise ValueError(f"Supply {field} filtering or explicitly attest {flag}")
    original = _read(source)
    with source.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream), [])
    if any(column not in headers for column in mapping.values()):
        raise ValueError("Mapped column is missing from source")
    accepted = []
    seen_ids: dict[str, dict] = {}
    seen_rows = set()
    for raw in original:
        value = lambda field: raw.get(mapping.get(field, ""), "").strip()
        if value("country").upper() not in INDONESIA:
            continue
        if any(config.get(field + "_values") and value(field).upper() not in {str(v).upper() for v in config[field + "_values"]}
               for field in ("status", "distance", "division")):
            continue
        if not re.fullmatch(r"\d+:[0-5]\d:[0-5]\d", value("time")):
            raise ValueError("Invalid finisher time in source; expected H:MM:SS")
        duration = pd.to_timedelta(value("time"), errors="coerce")
        if pd.isna(duration) or duration <= pd.Timedelta(0) or duration.total_seconds() % 1:
            raise ValueError("Invalid finisher time in source")
        row = {
            "Marathon": marathon, "Year": str(race_date.year), "Name": value("name").upper(),
            "Time": format_seconds_to_hms(duration.total_seconds()), "Place": value("place"),
            "Source_Result_ID": value("result_id"), "Source_URL": config["source_url"],
            "Race_Date": race_date.isoformat(), "Edition_Year": str(edition),
            "Country_Field": config["country_field_type"] + ":" + mapping["country"],
            "Country_Value": value("country"), "Time_Basis": config["time_basis"], "Place_Basis": config["place_basis"],
        }
        if row["Place"]:
            place = pd.to_numeric(row["Place"], errors="coerce")
            if pd.isna(place) or place <= 0 or place % 1:
                raise ValueError("Source place must be a positive whole number or blank")
            row["Place"] = str(int(place))
        if not row["Name"]:
            raise ValueError("Finisher name is blank")
        row["Record_Key"] = record_key(row)
        identity = row["Source_Result_ID"]
        if identity:
            if identity in seen_ids:
                if seen_ids[identity] != row:
                    raise ValueError("Conflicting rows share a source result ID")
                continue
            seen_ids[identity] = row
        elif row["Record_Key"] in seen_rows:
            raise ValueError("Duplicate result without a source ID requires review")
        seen_rows.add(row["Record_Key"])
        accepted.append(row)
    expected = config.get("expected_count")
    if expected is not None and (not isinstance(expected, int) or isinstance(expected, bool) or expected < 0):
        raise ValueError("expected_count must be a nonnegative integer")
    if expected is not None and expected != len(accepted):
        raise ValueError(f"Expected {expected} Indonesian finishers, imported {len(accepted)}")
    if not accepted and not (expected == 0 and config.get("completeness_verified") is True):
        raise ValueError("An empty import is not evidence of zero Indonesian finishers")
    complete = expected is not None and config.get("completeness_verified") is True
    stem = f"{marathon.lower()}-{edition}"
    legacy = data_dir / "legacy_results.csv"
    if legacy.exists() and any(r["Marathon"] == marathon and r["Year"] == str(race_date.year) for r in _read(legacy)):
        raise ValueError("Import overlaps protected legacy results; reconcile explicitly before replacing history")
    metadata = {
        "Marathon": marathon, "Year": race_date.year, "Edition_Year": edition,
        "Status": ("verified zero finishers" if not accepted else "complete") if complete else "partial",
        "Imported_Count": len(accepted), "Expected_Count": expected, "Source_URL": config["source_url"],
        "Retrieved_At": datetime.now(timezone.utc).isoformat(),
        "Note": config.get("note", "Counts reconciled with source." if complete else "Completeness not verified."),
        "Source_SHA256": hashlib.sha256(source.read_bytes()).hexdigest(), "Config": config,
    }
    _write(data_dir / "editions" / f"{stem}.csv", _csv(accepted, REQUIRED_COLUMNS + METADATA_COLUMNS))
    _write(data_dir / "editions" / f"{stem}.json", json.dumps(metadata, indent=2) + "\n")
    snapshot = data_dir / "sources" / f"{stem}.csv"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != snapshot.resolve():
        shutil.copyfile(source, snapshot)
    return metadata


def build(data_dir: Path = ROOT_DIR / "data", output: Path = ROOT_DIR / "raw_data.csv") -> dict:
    legacy = data_dir / "legacy_results.csv"
    # Loading validates the baseline before any generated output is changed.
    coverage = {(r["Marathon"], r["Year"]): r for r in initial_coverage(load_data(legacy))}
    rows = _read(legacy)
    metadata_rows = []
    partitions = set()
    for path in sorted((data_dir / "editions").glob("*.json")):
        edition = json.loads(path.read_text(encoding="utf-8"))
        key = (edition["Marathon"], edition["Year"])
        if key not in coverage or key in partitions or edition["Status"] not in STATUSES:
            raise ValueError(f"Invalid or duplicate edition partition: {path.name}")
        partition = _read(path.with_suffix(".csv"))
        if any(r["Marathon"] != key[0] or r["Year"] != str(key[1]) for r in partition):
            raise ValueError("Result rows do not match edition metadata")
        if any(r["Marathon"] == key[0] and r["Year"] == str(key[1]) for r in rows):
            raise ValueError("Edition overlaps protected results")
        if len(partition) != edition["Imported_Count"]:
            raise ValueError("Edition row count does not match metadata")
        if edition["Status"] in {"complete", "verified zero finishers"} and edition["Expected_Count"] != len(partition):
            raise ValueError("Complete edition has an unreconciled count")
        partitions.add(key)
        rows.extend(partition)
        metadata_rows.extend({c: r[c] for c in METADATA_COLUMNS} for r in partition)
        coverage[key] = {k: v for k, v in edition.items() if k not in {"Config", "Source_SHA256"}}
    rows.sort(key=lambda r: (int(r["Year"]), r["Marathon"], pd.to_timedelta(r["Time"]).total_seconds(), r["Name"], r["Place"]))
    csv_text = _csv(rows, REQUIRED_COLUMNS)
    if len({row["Record_Key"] for row in metadata_rows}) != len(metadata_rows):
        raise ValueError("Identical core results have ambiguous source identities; review before building")
    with tempfile.TemporaryDirectory() as directory:
        validation = Path(directory) / "validate.csv"
        validation.write_text(csv_text, encoding="utf-8")
        checked = load_data(validation)
    conflicts = checked.loc[checked.duplicated(["Marathon", "Year", "Name"], keep=False), REQUIRED_COLUMNS]
    _write(output, csv_text)
    _write(data_dir / "result_metadata.csv", _csv(metadata_rows, METADATA_COLUMNS))
    _write(data_dir / "coverage.json", json.dumps(list(coverage.values()), indent=2) + "\n")
    _write(data_dir / "conflicts.csv", conflicts.to_csv(index=False))
    return {"rows": len(rows), "imported_editions": len(partitions), "conflicting_rows": len(conflicts)}


def fetch(url: str, destination: Path) -> None:
    """Download an accessible CSV export; never guess or bypass protected APIs."""
    if not url.startswith("https://"):
        raise ValueError("Fetch requires an HTTPS CSV export URL")
    request = urllib.request.Request(url, headers={"User-Agent": "WMM-data-import/1.0", "Accept": "text/csv"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read().decode("utf-8-sig")
    if content.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError("Source returned HTML rather than a CSV export; use an authorised file export")
    reader = csv.reader(io.StringIO(content))
    if len(next(reader, [])) < 2:
        raise ValueError("Source did not return a CSV table")
    _write(destination, content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("fetch", help="Download a permitted direct CSV export")
    download.add_argument("url")
    download.add_argument("output", type=Path)
    ingest = commands.add_parser("import", help="Validate and store an edition using an explicit source mapping")
    ingest.add_argument("input", type=Path)
    ingest.add_argument("--config", required=True, type=Path)
    commands.add_parser("build", help="Build bundled results, provenance, coverage, and conflict report")
    commands.add_parser("validate", help="Validate the bundled dataset without changing files")
    collect = commands.add_parser("collect", help="Collect an edition from a supported official public source")
    collect.add_argument("provider", choices=["abbott", "boston"])
    collect.add_argument("marathon", choices=list(RACES))
    collect.add_argument("edition_year", type=int)
    collect.add_argument("--race-date", required=True, help="Actual race date, YYYY-MM-DD")
    commands.add_parser("collect-scheduled", help="Collect the editions in data/collection_schedule.json")
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            fetch(args.url, args.output)
            print(f"Saved CSV export to {args.output}")
        elif args.command == "import":
            result = import_edition(args.input, json.loads(args.config.read_text(encoding="utf-8")))
            print(json.dumps({k: v for k, v in result.items() if k != "Config"}, indent=2))
        elif args.command == "build":
            print(json.dumps(build(), indent=2))
        elif args.command == "collect":
            from .sources import collect_edition
            result = collect_edition(args.provider, args.marathon, args.edition_year, args.race_date)
            print(json.dumps({k: v for k, v in result.items() if k != "Config"}, indent=2))
        elif args.command == "collect-scheduled":
            from .sources import collect_edition
            failures = []
            schedule = json.loads((ROOT_DIR / "data" / "collection_schedule.json").read_text())
            for entry in schedule:
                label = f"{entry['marathon']} {entry['edition_year']}"
                try:
                    result = collect_edition(entry["provider"], entry["marathon"], entry["edition_year"], entry["race_date"])
                    print(f"{label}: {result['Imported_Count']} results ({result['Status']})", flush=True)
                except (ValueError, KeyError, OSError) as error:
                    failures.append(label)
                    print(f"{label}: not imported: {error}", flush=True)
            if failures:
                parser.exit(1, "Some editions were not imported: " + ", ".join(failures) + "\n")
        else:
            print(json.dumps({"rows": len(load_data()), "valid": True}))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"Import failed: {error}\n")


if __name__ == "__main__":
    main()
