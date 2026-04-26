from __future__ import annotations

import unittest

import pandas as pd

from src.wmm.metrics import (
    filtered_data,
    road_to_stars,
    runner_option_labels,
    runner_search_options,
    star_leaderboard,
    summary_metrics,
)


def sample_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Marathon": "Berlin",
                "Year": 2023,
                "Name": "ALICE RUNNER",
                "Time": "03:10:00",
                "Place": 101,
                "Time_seconds": 11400,
                "Time_HHMM": "03:10",
                "Indo_Place": 1,
            },
            {
                "Marathon": "Boston",
                "Year": 2024,
                "Name": "ALICE RUNNER",
                "Time": "03:05:00",
                "Place": 88,
                "Time_seconds": 11100,
                "Time_HHMM": "03:05",
                "Indo_Place": 1,
            },
            {
                "Marathon": "Chicago",
                "Year": 2024,
                "Name": "ALICE RUNNER",
                "Time": "03:00:00",
                "Place": 70,
                "Time_seconds": 10800,
                "Time_HHMM": "03:00",
                "Indo_Place": 1,
            },
            {
                "Marathon": "Berlin",
                "Year": 2024,
                "Name": "BOB RUNNER",
                "Time": "04:00:00",
                "Place": 400,
                "Time_seconds": 14400,
                "Time_HHMM": "04:00",
                "Indo_Place": 2,
            },
            {
                "Marathon": "Boston",
                "Year": 2024,
                "Name": "BOB RUNNER",
                "Time": "03:50:00",
                "Place": 350,
                "Time_seconds": 13800,
                "Time_HHMM": "03:50",
                "Indo_Place": 2,
            },
            {
                "Marathon": "Berlin",
                "Year": 2024,
                "Name": "CAROL RUNNER",
                "Time": "05:00:00",
                "Place": 1000,
                "Time_seconds": 18000,
                "Time_HHMM": "05:00",
                "Indo_Place": 3,
            },
        ]
    )


class MetricsTest(unittest.TestCase):
    def test_summary_metrics_uses_latest_year_and_fastest_result(self) -> None:
        metrics = summary_metrics(sample_results())

        self.assertEqual(metrics["rows"], 6)
        self.assertEqual(metrics["runners"], 3)
        self.assertEqual(metrics["marathons"], 3)
        self.assertEqual(metrics["year_range"], "2023-2024")
        self.assertEqual(metrics["latest_year"], 2024)
        self.assertEqual(metrics["latest_entries"], 5)
        self.assertEqual(metrics["entry_delta"], 4)
        self.assertEqual(metrics["fastest_label"], "ALICE RUNNER | Chicago 2024 | 03:00:00")

    def test_filtered_data_returns_only_selected_lens(self) -> None:
        filtered = filtered_data(sample_results(), ["Berlin"], 2024, 2024)

        self.assertEqual(filtered["Marathon"].tolist(), ["Berlin", "Berlin"])
        self.assertEqual(filtered["Name"].tolist(), ["BOB RUNNER", "CAROL RUNNER"])

    def test_road_to_stars_statuses_and_missing_majors(self) -> None:
        roadmap = road_to_stars(sample_results(), ["Berlin", "Boston", "Chicago"])
        rows = roadmap.set_index("Name")

        self.assertEqual(rows.loc["ALICE RUNNER", "Status"], "Complete")
        self.assertEqual(rows.loc["ALICE RUNNER", "Missing_Majors"], "None")
        self.assertEqual(rows.loc["BOB RUNNER", "Status"], "One away")
        self.assertEqual(rows.loc["BOB RUNNER", "Missing_Majors"], "Chicago")

    def test_runner_search_returns_names_and_labels_are_separate(self) -> None:
        df = sample_results()
        options = runner_search_options(df, "alice", limit=5)
        labels = runner_option_labels(df)

        self.assertEqual(options, ["ALICE RUNNER"])
        self.assertEqual(labels["ALICE RUNNER"], "ALICE RUNNER (3 entries, 3 stars)")
        self.assertNotIn("(", options[0])

    def test_star_leaderboard_orders_by_stars_then_entries(self) -> None:
        leaderboard = star_leaderboard(sample_results(), limit=2)

        self.assertEqual(leaderboard["Name"].tolist(), ["ALICE RUNNER", "BOB RUNNER"])
        self.assertEqual(leaderboard["Stars"].tolist(), [3, 2])
        self.assertEqual(leaderboard["Best_Time"].tolist(), ["03:00:00", "03:50:00"])


if __name__ == "__main__":
    unittest.main()
