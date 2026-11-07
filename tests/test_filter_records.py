"""在本目录执行：python -B -m unittest -v test_filter_records.py"""
import unittest
from copy import deepcopy

from filter_records import filter_records


class FilterRecordsTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            self.record("a", "2026-11-06", "expense", 10, "饮食", "2026-11-08T00:00:00Z"),
            self.record("b", "2026-11-07", "expense", 20, "饮食", "2026-11-07T09:00:00+08:00"),
            self.record("c", "2026-11-07", "expense", 30, "交通", "2026-11-07T02:00:00Z"),
            self.record("d", "2026-11-08", "income", 100, "工资", "2026-11-08T00:00:00Z"),
        ]

    @staticmethod
    def record(record_id, date, record_type, amount, category, created_at):
        return dict(id=record_id, date=date, type=record_type, amount=amount,
                    category=category, note="测试", created_at=created_at)

    def ids(self, **conditions):
        return [record["id"] for record in filter_records(self.records, **conditions)]

    def test_no_conditions_sort_and_preserve_input(self):
        original = deepcopy(self.records)
        result = filter_records(self.records)
        self.assertEqual(result, [original[3], original[2], original[1], original[0]])
        self.assertIsNot(result, self.records)
        self.assertEqual(self.records, original)
        result.clear()
        self.assertEqual(self.records, original)

    def test_individual_conditions_and_inclusive_boundaries(self):
        cases = [
            ({"start_date": "2026-11-07"}, ["d", "c", "b"]),
            ({"end_date": "2026-11-07"}, ["c", "b", "a"]),
            ({"category": "饮食"}, ["b", "a"]),
            ({"category": "饮"}, []),
            ({"category": ""}, []),
            ({"record_type": "income"}, ["d"]),
            ({"record_type": "expense"}, ["c", "b", "a"]),
            ({"min_amount": 20}, ["d", "c", "b"]),
            ({"max_amount": 20}, ["b", "a"]),
            ({"max_amount": 0}, []),
            ({"min_amount": 10**400}, []),
            ({"min_amount": 20, "max_amount": 20}, ["b"]),
            ({"start_date": "2026-11-07", "end_date": "2026-11-07"}, ["c", "b"]),
        ]
        for conditions, expected in cases:
            with self.subTest(conditions=conditions):
                self.assertEqual(self.ids(**conditions), expected)

    def test_all_conditions_are_combined_with_and(self):
        original = deepcopy(self.records)
        self.assertEqual(self.ids(
            start_date="2026-11-06", end_date="2026-11-07", category="饮食",
            record_type="expense", min_amount=20, max_amount=30,
        ), ["b"])
        self.assertEqual(self.records, original)

    def test_empty_and_no_matches(self):
        self.assertEqual(filter_records([]), [])
        self.assertEqual(self.ids(category="医疗"), [])
        self.assertEqual(self.ids(start_date="2028-02-29"), [])

    def test_invalid_conditions_raise_value_error(self):
        cases = [
            {"start_date": "2026-11-08", "end_date": "2026-11-07"},
            {"min_amount": 30, "max_amount": 20},
            {"start_date": "2026-02-29"}, {"end_date": "20261107"},
            {"start_date": "2026-1-7"}, {"end_date": 20261107},
            {"record_type": "支出"}, {"record_type": ""}, {"category": 1},
            {"min_amount": "20"}, {"max_amount": True},
            {"min_amount": float("nan")}, {"max_amount": float("inf")},
        ]
        for records in ([], self.records):
            for conditions in cases:
                with self.subTest(empty=not records, conditions=conditions):
                    with self.assertRaises(ValueError):
                        filter_records(records, **conditions)


if __name__ == "__main__":
    unittest.main()
