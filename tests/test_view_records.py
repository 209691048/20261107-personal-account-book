"""第 5 号模块验收：python -m unittest discover -s tests -p test_view_records.py"""
import unittest
from copy import deepcopy

from view_records import get_recent_records


class RecentRecordsTests(unittest.TestCase):
    def setUp(self):
        # 旧发生日期即使录入更晚，也应排在新发生日期之后。
        self.records = [
            self.record("older_date", "2026-11-06", "2026-11-08T07:00:00+00:00"),
            self.record("earlier", "2026-11-07", "2026-11-07T09:00:00+08:00"),
            self.record("latest", "2026-11-07", "2026-11-07T02:00:00Z"),
        ]

    @staticmethod
    def record(record_id, date, created_at):
        return {
            "id": record_id,
            "date": date,
            "type": "expense",
            "amount": 25.5,
            "category": "饮食",
            "note": "午餐",
            "created_at": created_at,
        }

    def test_date_then_actual_creation_time_descending(self):
        self.assertEqual(
            [record["id"] for record in get_recent_records(self.records)],
            ["latest", "earlier", "older_date"],
        )
        self.assertEqual(get_recent_records(self.records, 1), [self.records[2]])

    def test_default_limit_is_ten(self):
        records = [
            self.record(str(day), f"2026-11-{day:02d}", f"2026-11-{day:02d}T12:00:00+00:00")
            for day in range(1, 13)
        ]
        self.assertEqual(
            [record["id"] for record in get_recent_records(records)],
            [str(day) for day in range(12, 2, -1)],
        )

    def test_empty_zero_and_oversized_limits(self):
        self.assertEqual(get_recent_records([]), [])
        self.assertEqual(get_recent_records(self.records, 0), [])
        self.assertEqual(
            get_recent_records(self.records, 99),
            [self.records[2], self.records[1], self.records[0]],
        )

    def test_invalid_limits_raise_value_error_even_with_empty_input(self):
        for records in ([], self.records):
            for limit in (-1, True, False, 1.0, "1", None):
                with self.subTest(empty=not records, limit=limit):
                    with self.assertRaises(ValueError):
                        get_recent_records(records, limit)

    def test_input_and_all_record_fields_are_preserved(self):
        original = deepcopy(self.records)
        result = get_recent_records(self.records)
        self.assertEqual(self.records, original)
        self.assertEqual(result, [original[2], original[1], original[0]])
        self.assertIsNot(result, self.records)
        result.clear()
        self.assertEqual(self.records, original)


if __name__ == "__main__":
    unittest.main()
