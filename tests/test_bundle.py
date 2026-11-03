from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import shutil

from src.wmm.data import DATA_PATH, ROOT_DIR, load_data
from src.wmm.ingest import build


class BundledDataTest(unittest.TestCase):
    def test_every_original_result_is_retained(self):
        def rows(path):
            with path.open(newline="") as source:
                return Counter(tuple(row.values()) for row in csv.DictReader(source))
        original = rows(ROOT_DIR / "data" / "legacy_results.csv")
        bundled = rows(DATA_PATH)
        self.assertEqual(sum(original.values()), 5844)
        self.assertFalse(original - bundled)

    def test_source_snapshots_counts_and_provenance_reconcile(self):
        data_dir = ROOT_DIR / "data"
        imported_count = 0
        for path in (data_dir / "editions").glob("*.json"):
            metadata = json.loads(path.read_text())
            source = data_dir / "sources" / (path.stem + ".csv")
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), metadata["Source_SHA256"])
            imported_count += metadata["Imported_Count"]
        df = load_data()
        self.assertEqual(len(df), 5844 + imported_count)
        self.assertEqual(int(df["Source_URL"].notna().sum()), imported_count)
        self.assertEqual(set(df["Marathon"]), {"Berlin", "Boston", "Chicago", "London", "NYC", "Tokyo", "Sydney"})
        self.assertEqual(int(df["Year"].max()), 2026)

    def test_rebuilding_actual_bundle_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "data"
            shutil.copytree(ROOT_DIR / "data", data_dir)
            output = Path(directory) / "raw_data.csv"
            build(data_dir, output)
            self.assertEqual(output.read_bytes(), DATA_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
