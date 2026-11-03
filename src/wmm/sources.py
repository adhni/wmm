"""Adapters for official public result searches; no account credentials needed."""
from __future__ import annotations

import csv
import io
import json
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from .data import ROOT_DIR
from .ingest import import_edition

ABBOTT_SEARCH = "https://gxo3mfmtr4.execute-api.eu-west-1.amazonaws.com/raceresults/_search"
ABBOTT_PAGE = "https://www.worldmarathonmajors.com/six-star/claim-stars"
EVENT_TITLES = {
    "Berlin": "Berlin Marathon", "Boston": "Boston Marathon", "Chicago": "Chicago Marathon",
    "London": "London Marathon", "NYC": "New York City Marathon", "Tokyo": "Tokyo Marathon", "Sydney": "Sydney Marathon",
}
SOURCE_COLUMNS = ["Name", "Country", "Time", "Place", "Result_ID", "Status", "Division"]


def _request(url: str, body: dict, *, form: bool = False) -> str:
    payload = urllib.parse.urlencode(body).encode() if form else json.dumps(body).encode()
    request = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/x-www-form-urlencoded" if form else "application/json",
        "User-Agent": "WMM-data-import/1.0",
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8-sig")


def abbott_results(marathon: str, edition: int, race_date: str) -> tuple[list[dict], dict]:
    """Reconcile every page against an exact public-index hit count.

    The index is the one used by Abbott's own Claim Stars UI. Index completeness
    is distinct from independent reconciliation against a race organiser's list.
    """
    filters = [
        {"term": {"nationality.keyword": "INA"}},
        {"term": {"result_type.keyword": "Six Star"}},
        {"term": {"event_title.keyword": EVENT_TITLES[marathon]}},
        {"terms": {"result_year": sorted({edition, int(race_date[:4])})}},
    ]
    rows = []
    ids = set()
    offset = 0
    total = None
    while total is None or offset < total:
        body = {
            "from": offset, "size": 500, "track_total_hits": True,
            "_source": ["result_id", "firstname", "lastname", "fullname", "nationality", "event_title", "result_year", "result_type", "finish_time", "place", "race_title"],
            "sort": [{"result_id.keyword": "asc"}], "query": {"bool": {"filter": filters}},
        }
        response = json.loads(_request(ABBOTT_SEARCH, body))
        if response.get("timed_out") or response.get("_shards", {}).get("failed", 0):
            raise ValueError("Abbott search was incomplete; retry before importing")
        hits = response["hits"]
        if hits["total"]["relation"] != "eq":
            raise ValueError("Abbott did not provide an exact count")
        if total is None:
            total = hits["total"]["value"]
            if total > 10000:
                raise ValueError("Edition exceeds the search pagination window; use an export")
        elif total != hits["total"]["value"]:
            raise ValueError("Abbott result count changed during collection; retry")
        batch = hits["hits"]
        if not batch and offset < total:
            raise ValueError("Abbott pagination ended before the reported count")
        for hit in batch:
            source = hit["_source"]
            identity = str(source["result_id"])
            if identity in ids:
                raise ValueError("Abbott repeated a result across pages")
            if source["nationality"] != "INA" or source["event_title"] != EVENT_TITLES[marathon] or source["result_type"] != "Six Star":
                raise ValueError("Abbott returned a record outside the requested cohort")
            if int(source["result_year"]) not in {edition, int(race_date[:4])}:
                raise ValueError("Abbott returned a record outside the requested year")
            ids.add(identity)
            name = " ".join(filter(None, [source.get("firstname", "").strip(), source.get("lastname", "").strip()])) or source["fullname"]
            place = source.get("place")
            rows.append({
                "Name": name, "Country": "INA", "Time": source["finish_time"],
                "Place": str(place) if place and int(place) > 0 else "", "Result_ID": identity,
                "Status": "FINISHED", "Division": "RUNNING",
            })
        offset += len(batch)
    config = source_config(marathon, edition, race_date, ABBOTT_PAGE, "nationality")
    config.update(expected_count=total, completeness_verified=False,
                  note=f"All {total} nationality=INA Six Star records in Abbott's public result index retrieved. Race-organiser completeness and placing scope not independently verified.",
                  search_url=ABBOTT_SEARCH, source_count=total)
    return rows, config


def boston_results(edition: int, race_date: str) -> tuple[list[dict], dict]:
    if edition not in (2025, 2026):
        raise ValueError("Boston adapter is verified for 2025 and 2026 only")
    url = f"https://registration.baa.org/{edition}/cf/Media/iframe_ResultsSearch.cfm?mode=advanceddetail"
    fields = {"VarTargetCount": "0", "CountryOfCtzID": "85"}
    report = _request(url, {**fields, "DisplayType": "browser"}, form=True)
    text = re.sub(r"<[^>]*>", " ", report)
    match = re.search(r"Your\s+search\s+returned\s+(\d+)\s+athlete", text, re.I)
    if not match:
        raise ValueError("Boston did not provide its query count; source format may have changed")
    reader = csv.DictReader(io.StringIO(_request(url, {**fields, "DisplayType": "csv"}, form=True)))
    exported = list(reader)
    if len(exported) != int(match[1]):
        raise ValueError("Boston CSV count differs from its official search count")
    required = {"FullName", "CountryOfCtzAbbrev", "OfficialTime", "RankOverall", "BibNumber", "EventGroup"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Boston CSV headers have changed")
    rows = []
    for source in exported:
        if source["CountryOfCtzAbbrev"] != "INA":
            raise ValueError("Boston returned a non-Indonesian citizenship record")
        if source["EventGroup"] != "Runners" or not re.fullmatch(r"\d+:[0-5]\d:[0-5]\d", source["OfficialTime"]):
            continue
        rows.append({
            "Name": source["FullName"], "Country": "INA", "Time": source["OfficialTime"],
            "Place": source["RankOverall"], "Result_ID": source["BibNumber"],
            "Status": "FINISHED", "Division": "RUNNING",
        })
    config = source_config("Boston", edition, race_date, url, "citizenship")
    config.update(expected_count=len(rows), completeness_verified=True, place_basis="overall",
                  source_count=int(match[1]), note=f"CSV reconciled to {match[1]} official citizenship=Indonesia search records; {len(rows)} running finishers retained. Unneeded address and demographic columns omitted.")
    return rows, config


def source_config(marathon: str, edition: int, race_date: str, url: str, country_type: str) -> dict:
    return {
        "marathon": marathon, "edition_year": edition, "race_date": race_date,
        "source_url": url, "country_field_type": country_type, "time_basis": "official", "place_basis": "unknown",
        "columns": {"name": "Name", "country": "Country", "time": "Time", "place": "Place", "result_id": "Result_ID", "status": "Status", "division": "Division"},
        "status_values": ["FINISHED"], "division_values": ["RUNNING"], "marathon_only": True,
    }


def collect_edition(provider: str, marathon: str, edition: int, race_date: str, data_dir: Path = ROOT_DIR / "data") -> dict:
    if provider == "boston":
        if marathon != "Boston":
            raise ValueError("Boston provider only supports Boston")
        rows, config = boston_results(edition, race_date)
    elif provider == "abbott":
        rows, config = abbott_results(marathon, edition, race_date)
    else:
        raise ValueError("Unsupported provider")
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "results.csv"
        with source.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=SOURCE_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return import_edition(source, config, data_dir)
