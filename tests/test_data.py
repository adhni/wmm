from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.wmm.data import load_data


class LoadDataTest(unittest.TestCase):
    def test_load_data_normalizes_names_and_adds_rank_columns(self) -> None:
        csv_text = "\n".join(
            [
                "Marathon,Year,Name,Time,Place",
                "Berlin,2024, alice runner ,03:10:00,101",
                "Berlin,2024,Bob Runner,03:05:00,88",
                "Berlin,2024,Carol Runner,03:05:00,90",
                "Boston,2023,Alice Runner,04:15:30,500",
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "raw_data.csv"
            path.write_text(csv_text)

            df = load_data(path)

        self.assertEqual(list(df.columns), [
            "Marathon",
            "Year",
            "Name",
            "Time",
            "Place",
            "Time_seconds",
            "Time_HHMM",
            "Indo_Place",
        ])
        self.assertEqual(df.loc[df["Name"].str.contains("ALICE"), "Name"].tolist(), [
            "ALICE RUNNER",
            "ALICE RUNNER",
        ])
        self.assertEqual(df["Year"].dtype.kind, "i")
        self.assertEqual(df["Place"].dtype.kind, "i")
        self.assertEqual(int(df.loc[df["Time"] == "04:15:30", "Time_seconds"].iloc[0]), 15330)
        self.assertEqual(df.loc[df["Time"] == "04:15:30", "Time_HHMM"].iloc[0], "04:15")

        berlin = df.loc[df["Marathon"] == "Berlin"].sort_values(["Time_seconds", "Name"])
        self.assertEqual(berlin["Indo_Place"].tolist(), [1, 1, 2])


if __name__ == "__main__":
    unittest.main()
