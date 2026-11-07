"""第 10 号模块的 CSV 导出验收测试。"""

import codecs
import csv
from copy import deepcopy
from io import StringIO
import unittest

from export_data import export_csv


_FIELDS = ["id", "date", "type", "amount", "category", "note", "created_at"]


class ExportCsvTests(unittest.TestCase):
    def test_export_preserves_fields_and_input_order(self):
        note = '午餐, "双人份"\n含饮料'
        records = [
            {
                "note": note,
                "category": "饮食",
                "amount": 25.5,
                "id": "expense-1",
                "date": "2026-11-07",
                "type": "expense",
                "created_at": "2026-11-07T06:30:00+00:00",
            },
            {
                "id": "income-1",
                "date": "2026-11-06",
                "type": "income",
                "amount": 100,
                "category": "兼职",
                "local_metadata": "旧版扩展字段",
            },
        ]
        original = deepcopy(records)

        data = export_csv(records)

        self.assertIsInstance(data, bytes)
        self.assertTrue(data.startswith(codecs.BOM_UTF8))
        rows = list(csv.reader(StringIO(data.decode("utf-8-sig"), newline="")))
        self.assertEqual(rows, [
            _FIELDS,
            ["expense-1", "2026-11-07", "expense", "25.5", "饮食", note,
             "2026-11-07T06:30:00+00:00"],
            ["income-1", "2026-11-06", "income", "100", "兼职", "", ""],
        ])
        self.assertEqual(records, original)

    def test_empty_export_has_only_header(self):
        header = ",".join(_FIELDS) + "\r\n"
        self.assertEqual(export_csv([]), header.encode("utf-8-sig"))

    def test_formula_like_text_is_escaped_without_changing_source(self):
        note = '  =SUM(1,2);"text"'
        record = {"id": "@id", "amount": 3, "note": note}
        data = export_csv([record]).decode("utf-8-sig")
        row = next(csv.DictReader(StringIO(data, newline="")))
        self.assertEqual(row["id"], "'@id")
        self.assertEqual(row["note"], "'" + note)
        self.assertEqual(row["amount"], "3")
        self.assertEqual(record["note"], note)
