"""add_record.py 的流程测试，不依赖团队 storage.py 的真实文件。"""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import add_record as add_record_module


class AddRecordTests(unittest.TestCase):
    def test_appends_new_record_and_returns_it(self) -> None:
        existing = {
            "id": "a" * 32,
            "date": "2026-11-06",
            "type": "income",
            "amount": 50.0,
            "category": "兼职",
            "note": "旧记录",
            "created_at": "2026-11-06T06:00:00+00:00",
        }
        saved_records: list[dict] = []

        with (
            patch.object(add_record_module, "_load_records", return_value=[existing]),
            patch.object(
                add_record_module,
                "_save_records",
                side_effect=lambda records: saved_records.extend(records),
            ),
        ):
            result = add_record_module.add_record(
                "2026-11-07", "expense", 25.5, "饮食", "午餐"
            )

        self.assertEqual(len(saved_records), 2)
        self.assertEqual(saved_records[0], existing)
        self.assertEqual(saved_records[1], result)
        self.assertNotEqual(saved_records[0]["id"], saved_records[1]["id"])
        self.assertEqual(result["type"], "expense")
        self.assertEqual(result["amount"], 25.5)

    def test_validation_happens_before_loading_or_saving(self) -> None:
        load_mock = Mock()
        save_mock = Mock()

        with (
            patch.object(add_record_module, "_load_records", load_mock),
            patch.object(add_record_module, "_save_records", save_mock),
        ):
            with self.assertRaisesRegex(ValueError, "income 或 expense"):
                add_record_module.add_record(
                    "2026-11-07", "收入", 100.0, "工资"
                )

        load_mock.assert_not_called()
        save_mock.assert_not_called()

    def test_load_must_return_list(self) -> None:
        save_mock = Mock()
        with (
            patch.object(add_record_module, "_load_records", return_value={}),
            patch.object(add_record_module, "_save_records", save_mock),
        ):
            with self.assertRaisesRegex(ValueError, "记录列表"):
                add_record_module.add_record(
                    "2026-11-07", "income", 100.0, "工资"
                )

        save_mock.assert_not_called()

    def test_save_error_is_not_swallowed(self) -> None:
        with (
            patch.object(add_record_module, "_load_records", return_value=[]),
            patch.object(
                add_record_module,
                "_save_records",
                side_effect=OSError("磁盘写入失败"),
            ),
        ):
            with self.assertRaisesRegex(OSError, "磁盘写入失败"):
                add_record_module.add_record(
                    "2026-11-07", "income", 100.0, "工资"
                )

    def test_loaded_list_is_not_mutated(self) -> None:
        original_records: list[dict] = []
        with (
            patch.object(
                add_record_module, "_load_records", return_value=original_records
            ),
            patch.object(add_record_module, "_save_records"),
        ):
            add_record_module.add_record(
                "2026-11-07", "income", 100.0, "工资"
            )

        self.assertEqual(original_records, [])


if __name__ == "__main__":
    unittest.main()
