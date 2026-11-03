from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.wmm.catalog import SIX_STAR, SEVEN_RACES
from src.wmm.coverage import comparable_years
from src.wmm.data import format_place, load_data
from src.wmm.ingest import build, import_edition
from src.wmm.metrics import fastest_by_marathon, finish_time_spectrum, road_to_stars, runner_milestones, runner_next_goals, runner_summary, runner_year_in_review, star_table


class ImportTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = self.root / "data"
        self.data.mkdir()
        (self.data / "legacy_results.csv").write_text("Marathon,Year,Name,Time,Place\nBerlin,2024,LEGACY RUNNER,3:10:00,1\n")
        self.source = self.root / "source.csv"
        self.config = {
            "marathon": "Tokyo", "edition_year": 2026, "race_date": "2026-03-01",
            "source_url": "https://example.org/official-results", "country_field_type": "nationality",
            "time_basis": "net", "place_basis": "overall",
            "columns": {"name": "Name", "country": "Country", "time": "Time", "place": "Place", "result_id": "ID", "status": "Status", "distance": "Distance", "division": "Division"},
            "status_values": ["FINISHED"], "distance_values": ["MARATHON"], "division_values": ["RUNNING"],
        }

    def source_rows(self, rows=None):
        default = {"Name": "New Runner", "Country": "INA", "Time": "3:00:00", "Place": "", "ID": "100", "Status": "FINISHED", "Distance": "MARATHON", "Division": "RUNNING"}
        with self.source.open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(default))
            writer.writeheader()
            writer.writerows([{**default, **r} for r in (rows if rows is not None else [{}])])

    def test_filters_country_distance_division_and_status(self):
        self.source_rows([{}, {"Country": "USA"}, {"Status": "DNF"}, {"Distance": "10K"}, {"Division": "WHEELCHAIR"}])
        result = import_edition(self.source, self.config, self.data)
        self.assertEqual(result["Imported_Count"], 1)
        self.assertEqual(result["Status"], "partial")
        build(self.data, self.root / "output.csv")
        df = load_data(self.root / "output.csv")
        self.assertEqual(len(df), 2)
        runner = df.loc[df["Name"].eq("NEW RUNNER")]
        self.assertEqual(runner_summary(runner, "NEW RUNNER")["best_result"].split("source place ")[-1], "—")
        self.assertEqual(format_place(runner.iloc[0]["Place"]), "—")

    def test_reimport_and_build_are_idempotent_and_keep_legacy(self):
        self.source_rows()
        self.config.update(expected_count=1, completeness_verified=True)
        for _ in range(2):
            import_edition(self.source, self.config, self.data)
            build(self.data, self.root / "output.csv")
            current = (self.root / "output.csv").read_bytes()
            if _ == 0:
                previous = current
        self.assertEqual(current, previous)
        self.assertIn(b"LEGACY RUNNER,3:10:00,1", current)
        coverage = json.loads((self.data / "coverage.json").read_text())
        tokyo = next(r for r in coverage if r["Marathon"] == "Tokyo" and r["Year"] == 2026)
        self.assertEqual(tokyo["Status"], "complete")

    def test_wrong_expected_count_does_not_write_edition(self):
        self.source_rows()
        self.config["expected_count"] = 2
        with self.assertRaisesRegex(ValueError, "Expected 2"):
            import_edition(self.source, self.config, self.data)
        self.assertFalse((self.data / "editions").exists())

    def test_empty_requires_explicit_zero_verification(self):
        self.source_rows([])
        with self.assertRaisesRegex(ValueError, "empty import"):
            import_edition(self.source, self.config, self.data)
        self.config.update(expected_count=0, completeness_verified=True)
        result = import_edition(self.source, self.config, self.data)
        self.assertEqual(result["Status"], "verified zero finishers")
        build(self.data, self.root / "output.csv")
        self.assertEqual(len(load_data(self.root / "output.csv")), 1)

    def test_source_ids_deduplicate_but_conflicting_ids_fail(self):
        self.source_rows([{}, {}])
        self.assertEqual(import_edition(self.source, self.config, self.data)["Imported_Count"], 1)
        self.source_rows([{}, {"Time": "4:00:00"}])
        with self.assertRaisesRegex(ValueError, "Conflicting rows"):
            import_edition(self.source, self.config, self.data)

    def test_postponed_tokyo_uses_race_date_year(self):
        self.source_rows()
        self.config.update(edition_year=2021, race_date="2022-03-06")
        self.assertEqual(import_edition(self.source, self.config, self.data)["Year"], 2022)
        build(self.data, self.root / "output.csv")
        df = load_data(self.root / "output.csv")
        self.assertEqual(df.loc[df["Marathon"].eq("Tokyo"), "Year"].tolist(), [2022])

    def test_missing_country_mapping_and_unverified_division_fail(self):
        self.source_rows()
        del self.config["columns"]["country"]
        with self.assertRaisesRegex(ValueError, "Map name, country"):
            import_edition(self.source, self.config, self.data)

    def test_legacy_overlap_is_rejected(self):
        self.source_rows()
        self.config.update(marathon="Berlin", edition_year=2024, race_date="2024-09-29")
        with self.assertRaisesRegex(ValueError, "protected legacy"):
            import_edition(self.source, self.config, self.data)

    def test_invalid_times_and_places_do_not_enter_results(self):
        for overrides in ({"Time": "DNF"}, {"Time": "00:00:00"}, {"Time": "03:60:01"}, {"Time": "123"}, {"Place": "-1"}, {"Place": "1.5"}):
            self.source_rows([overrides])
            with self.assertRaises(ValueError):
                import_edition(self.source, self.config, self.data)


class JourneyTest(unittest.TestCase):
    def all_races(self):
        return pd.DataFrame([{"Marathon": m, "Year": 2026, "Name": "RUNNER", "Time": "03:00:00", "Place": pd.NA, "Time_seconds": 10800, "Indo_Place": 1} for m in SEVEN_RACES])

    def test_six_and_seven_are_separate_fixed_targets(self):
        df = self.all_races()
        original = road_to_stars(df, list(SIX_STAR)).iloc[0]
        self.assertEqual(original["Stars"], 6)
        self.assertEqual(original["Status"], "Complete")
        without_sydney = df.loc[df["Marathon"].ne("Sydney")]
        expanded = road_to_stars(without_sydney, list(SEVEN_RACES)).iloc[0]
        self.assertEqual(expanded["Status"], "One away")
        self.assertEqual(expanded["Missing_Majors"], "Sydney")

    def test_sydney_does_not_inflate_six_star_milestones_or_year_review(self):
        df = self.all_races().loc[lambda d: d["Marathon"].ne("Tokyo")]
        marks = runner_milestones(df, "RUNNER", list(SIX_STAR))
        self.assertNotIn("Reached 6 stars", marks["Milestone"].tolist())
        review = runner_year_in_review(df, "RUNNER", 2026, list(SIX_STAR))
        self.assertEqual(review["Stars_After_Year"], 5)
        self.assertIn("Sydney", review["Marathons"])

    def test_stars_export_counts_selected_journey_including_zero_star_runners(self):
        df = self.all_races()
        self.assertEqual(star_table(df, list(SIX_STAR)).iloc[0]["Stars"], 6)
        self.assertEqual(star_table(df, list(SEVEN_RACES)).iloc[0]["Stars"], 7)
        sydney_only = df.loc[df["Marathon"].eq("Sydney")]
        original_six = star_table(sydney_only, list(SIX_STAR))
        self.assertEqual(original_six.iloc[0]["Stars"], 0)
        self.assertNotIn("Sydney", original_six.columns)

    def test_fastest_row_never_borrows_slower_runners_place(self):
        df = self.all_races().head(1)
        slower = df.copy()
        slower["Time_seconds"] = 12000
        slower["Time"] = "03:20:00"
        slower["Place"] = 999
        result = fastest_by_marathon(pd.concat([df, slower]))
        self.assertTrue(pd.isna(result.iloc[0]["Place"]))

    def test_growth_only_compares_complete_same_race_cohorts(self):
        rows = [{"Marathon": m, "Year": y, "Status": "complete"} for m in ("Tokyo", "Sydney") for y in (2025, 2026)]
        coverage = pd.DataFrame(rows)
        self.assertTrue(comparable_years(coverage, ["Tokyo", "Sydney"], 2026))
        coverage.loc[0, "Status"] = "partial"
        self.assertFalse(comparable_years(coverage, ["Tokyo", "Sydney"], 2026))

    def test_spectrum_keeps_fast_and_slow_finishes(self):
        df = self.all_races().head(3).copy()
        df["Time_seconds"] = [8658, 10800, 34874]
        self.assertEqual(finish_time_spectrum(df)["Runner_Count"].sum(), len(df))

    def test_fast_runner_gets_a_goal_faster_than_existing_pb(self):
        df = self.all_races().copy()
        df["Time_seconds"] = 8658
        goals = runner_next_goals(df, "RUNNER", list(SIX_STAR))
        pb = goals.loc[goals["Goal"].eq("Time target")]
        self.assertFalse(pb.empty)
        self.assertIn("02:20", str(pb.iloc[0]["Target"]))


if __name__ == "__main__":
    unittest.main()
