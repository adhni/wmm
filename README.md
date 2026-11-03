# WMM

Streamlit dashboard for exploring Indonesian runners in the World Marathon Majors dataset.

Live app: https://wmm-id.streamlit.app/

## Data

- Current bundle, retrieved on **3 November 2026**: **13,432 results**, **7,832 distinct runner names**, **2012–2026**.
- All 5,844 original results from `posts/WMM` are preserved in `data/legacy_results.csv`.
- `raw_data.csv` is the generated dashboard input. Its core columns remain `Marathon`, `Year`, `Name`, `Time`, `Place`; unavailable placing is blank.
- `data/editions/` holds 24 imported race editions and their source mappings, checksums, counts, and retrieval dates. `data/sources/` holds the corresponding minimal source exports.
- `data/result_metadata.csv` adds source result IDs, URLs, race dates, edition labels, country-field meanings, timing basis, and placing basis to imported results when loaded by the app.
- `data/coverage.json` distinguishes complete, partial, unavailable, verified-zero, and not-held editions. Missing records do **not** establish zero participation.

| Race | Results | Bundled calendar years |
| --- | ---: | --- |
| Berlin | 4,446 | 2015–2026, excluding 2020 |
| Boston | 288 | 2015–2026, excluding 2020 |
| Chicago | 2,102 | 2012–2026, excluding 2020 |
| London | 1,037 | 2015–2026, excluding 2020 |
| NYC | 1,148 | 2015–2026, excluding 2020 |
| Tokyo | 1,743 | 2013–2019 and 2022–2026 |
| Sydney | 2,668 | 2025–2026 |

### Sources and limitations

The new Berlin, Chicago, London, NYC, Tokyo, and Sydney records come from the public search backing [Abbott's Claim Stars page](https://www.worldmarathonmajors.com/six-star/claim-stars). The adapter requests only the selected race, edition, nationality `INA`, and `Six Star` result type. That source type is also used for Sydney; it is a provider classification, not this app's journey target. Every page is reconciled to an exact index hit count, without requiring a runner account.

Boston 2025–2026 use the [official B.A.A. results export](https://registration.baa.org/2026/cf/Media/iframe_ResultsSearch.cfm?mode=advanced), filtered by Indonesian citizenship. Each year's CSV reconciles to its reported search count, with 60 running finishers retained per year. Address and demographic columns are omitted from the saved exports.

Boston's two new editions are marked complete. Abbott imports remain **partial** because retrieving every published index record does not independently establish completeness against the race organiser's full results. The original data's completeness and source retrieval dates are unknown. New records retain the source's official finish time; do not assume all editions use the same net/gun timing or overall/gender placing basis. Abbott placing `0` means unavailable and is stored as blank, with its placing basis marked unknown.

Runner histories are still matched by uppercase, trimmed name, not a verified person ID. `data/conflicts.csv` flags 22 rows with repeated names in the same race/year; these remain available for review. Source result IDs prevent repeated imports from duplicating records but do not resolve namesakes across races.

Tokyo's [2021 edition was held on 6 March 2022](https://www.marathon.tokyo/en/about/past/2021/news/detail/news_002235.html). Its four imported results appear under calendar year 2022 while retaining edition year 2021. There was no separate 2022 edition. Sydney starts at 2025; the exceptional 2024 Age Group World Championship stars are outside this backfill.

### Refresh data

Run these maintainer commands from the repository root; Streamlit itself makes no result-source requests:

```bash
python3 -m src.wmm.ingest collect-scheduled
python3 -m src.wmm.ingest build
python3 -m src.wmm.ingest validate
python3 -m unittest discover -s tests
```

`collect-scheduled` reads `data/collection_schedule.json`. It imports each edition independently and exits with an error if any source fails; previously imported editions remain available. Inspect failures and coverage before building or deploying. Network access is needed only for collection or direct CSV downloads. Public source interfaces can change; errors, repeated pages, changing counts, and truncated exports must be resolved before an edition is replaced.

To refresh one edition:

```bash
python3 -m src.wmm.ingest collect abbott Tokyo 2026 --race-date 2026-03-01
python3 -m src.wmm.ingest collect boston Boston 2026 --race-date 2026-04-20
```

For a permitted direct CSV export or manually supplied file:

```bash
python3 -m src.wmm.ingest fetch 'https://provider.example/results.csv' /tmp/results.csv
python3 -m src.wmm.ingest import /tmp/results.csv --config /tmp/import-config.json
python3 -m src.wmm.ingest build
```

Start with an edition's `Config` object, or `data/import-config.example.json`, and map the actual provider headers. Declare the country-field meaning, time and placing basis, and status/distance/division filters. Only set `completeness_verified` after reconciling the expected Indonesian finisher count with a complete official source. An empty export alone is never accepted as verified zero. Imports overlapping protected legacy race/year partitions are rejected rather than silently replacing history.

Builds preserve original records, produce deterministic output, and report same-name conflicts. Review `raw_data.csv`, provenance, coverage, and conflicts together, then restart the local app or deploy the updated bundle.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Test

```bash
python3 -m unittest discover -s tests
```

## Current Dashboard

- Filter by marathon and year range
- Track participation pulse, latest-year snapshots, and rank drift
- Explore separate **Original Six** and **Seven races covered** journeys, defaulting to Original Six
- Journey completion, passports, badges, and milestones use full recorded history and fixed race targets; sidebar filters select the displayed participants without changing journey requirements
- Completion means all target races are recorded in this dataset, not verified official medal status; the [original Six-Star programme excludes Sydney](https://www.worldmarathonmajors.com/sydney-major)
- Inspect source coverage and retrieval dates; annual growth deltas are shown only for comparable complete editions
- Browse `Hall of Fame` badges and leaderboards
- View marathon-specific profiles and finish-time fingerprints
- Search runner journeys, milestones, Indo ranks, and course mix
- Download filtered data, stars tables, and runner logs

## Project Layout

- `app.py`: Streamlit app entrypoint
- `src/wmm/data.py`: data loading and time formatting
- `src/wmm/metrics.py`: reusable analysis tables for the dashboard
- `src/wmm/catalog.py`: shared races, colours, and journey targets
- `src/wmm/ingest.py`, `sources.py`, `coverage.py`: collection, import, build, and coverage checks
- `.streamlit/config.toml`: Streamlit theme and server config

## Live Deployment

- Streamlit Community Cloud: https://wmm-id.streamlit.app/
