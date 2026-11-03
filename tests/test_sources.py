from __future__ import annotations

import csv
import io
import json
import unittest
from unittest.mock import patch

from src.wmm.sources import abbott_results, boston_results


def hit(identity, name="RUNNER", year=2026):
    return {"_source": {"result_id": identity, "firstname": name, "lastname": "", "fullname": name,
                        "nationality": "INA", "result_type": "Six Star", "event_title": "Tokyo Marathon",
                        "result_year": year, "finish_time": "03:00:00", "place": 0, "race_title": "Tokyo Marathon"}}


def page(hits, total, relation="eq"):
    return json.dumps({"hits": {"total": {"value": total, "relation": relation}, "hits": hits}, "_shards": {"failed": 0}})


class SourcesTest(unittest.TestCase):
    @patch("src.wmm.sources._request")
    def test_abbott_reconciles_all_pages_and_keeps_unknown_place_blank(self, request):
        request.side_effect = [page([hit("one")], 2), page([hit("two")], 2)]
        rows, config = abbott_results("Tokyo", 2026, "2026-03-01")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Place"], "")
        self.assertEqual(config["expected_count"], 2)
        self.assertFalse(config["completeness_verified"])
        self.assertEqual(request.call_args_list[1].args[1]["from"], 1)

    @patch("src.wmm.sources._request")
    def test_abbott_rejects_truncated_repeated_or_changing_pages(self, request):
        for responses in ([page([hit("one")], 2), page([], 2)],
                          [page([hit("one")], 2), page([hit("one")], 2)],
                          [page([hit("one")], 2), page([hit("two")], 3)],
                          [page([], 10000, "gte")]):
            request.side_effect = responses
            with self.assertRaises(ValueError):
                abbott_results("Tokyo", 2026, "2026-03-01")

    @patch("src.wmm.sources._request")
    def test_boston_reconciles_query_count_and_removes_non_running_results(self, request):
        output = io.StringIO()
        fields = ["FullName", "CountryOfCtzAbbrev", "OfficialTime", "RankOverall", "BibNumber", "EventGroup", "Zip"]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        base = dict(zip(fields, ["Runner", "INA", "3:00:00", "100", "42", "Runners", "PRIVATE"]))
        writer.writerows([base, {**base, "BibNumber": "43", "OfficialTime": ""}, {**base, "BibNumber": "44", "EventGroup": "Wheelchair"}])
        request.side_effect = ["Your search returned 3 athlete(s).", output.getvalue()]
        rows, config = boston_results(2026, "2026-04-20")
        self.assertEqual(len(rows), 1)
        self.assertNotIn("Zip", rows[0])
        self.assertTrue(config["completeness_verified"])
        self.assertEqual(config["expected_count"], 1)

    @patch("src.wmm.sources._request")
    def test_boston_incomplete_export_is_rejected(self, request):
        request.side_effect = ["Your search returned 2 athlete(s).", "FullName,CountryOfCtzAbbrev\nRunner,INA\n"]
        with self.assertRaisesRegex(ValueError, "CSV count"):
            boston_results(2026, "2026-04-20")


if __name__ == "__main__":
    unittest.main()
