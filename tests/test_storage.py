"""使用临时目录验证存储行为，不修改真实的 data/records.json。"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from add_record import add_record
from manage_records import delete_record, update_record
import storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.directory = Path(self.temporary_directory.name)
        self.data_file = self.directory / "data" / "records.json"
        self.addCleanup(patch.stopall)
        patch.object(storage, "_DATA_FILE", self.data_file).start()

    def sample_record(self, **updates):
        record = {
            "id": "e19b216d8b364be89dc9e2492ef08aca",
            "date": "2026-11-07",
            "type": "expense",
            "amount": 25.5,
            "category": "饮食",
            "note": "午餐，含饮料\n备注第二行",
            "created_at": "2026-11-07T06:30:00+00:00",
        }
        record.update(updates)
        return record

    def write_raw(self, content):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_bytes(content)

    def test_missing_file_returns_empty_without_creating_file(self):
        self.assertEqual(storage.load_records(), [])
        self.assertFalse(self.data_file.exists())
        self.assertFalse(self.data_file.parent.exists())

    def test_reads_utf8_bom_written_by_other_editors(self):
        records = [self.sample_record()]
        self.write_raw(json.dumps(records, ensure_ascii=False).encode("utf-8-sig"))
        self.assertEqual(storage.load_records(), records)

    def test_save_creates_directory_and_round_trips_chinese_records(self):
        records = [
            self.sample_record(),
            self.sample_record(id="another-id", type="income", category="工资"),
        ]
        before = json.dumps(records, ensure_ascii=False)

        self.assertIsNone(storage.save_records(records))

        self.assertEqual(storage.load_records(), records)
        text = self.data_file.read_text(encoding="utf-8")
        self.assertIn("饮食", text)
        self.assertIn('\n  {\n    "id":', text)
        self.assertIsInstance(json.loads(text)[0]["amount"], float)
        self.assertEqual(json.dumps(records, ensure_ascii=False), before)
        self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])

    def test_empty_list_can_replace_valid_records(self):
        storage.save_records([self.sample_record()])
        storage.save_records([])
        self.assertEqual(storage.load_records(), [])
        self.assertEqual(self.data_file.read_text(encoding="utf-8").strip(), "[]")

    def test_save_replaces_valid_records_instead_of_appending(self):
        storage.save_records([self.sample_record()])
        replacement = [self.sample_record(id="replacement", amount=100.0)]
        storage.save_records(replacement)
        self.assertEqual(storage.load_records(), replacement)

    def test_invalid_json_raises_without_changing_original(self):
        for original in (b"", b"[", b'{"unfinished":', b"[] garbage"):
            with self.subTest(original=original):
                self.write_raw(original)
                with self.assertRaises(ValueError):
                    storage.load_records()
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_invalid_utf8_raises_without_changing_original(self):
        original = b"[\xff]"
        self.write_raw(original)
        with self.assertRaises(ValueError):
            storage.load_records()
        self.assertEqual(self.data_file.read_bytes(), original)

    def test_invalid_record_and_duplicate_id_block_reads_and_writes(self):
        valid = self.sample_record()
        for records in ([self.sample_record(amount="25.50")], [valid, valid]):
            with self.subTest(records=records):
                original = json.dumps(records).encode("utf-8")
                self.write_raw(original)
                with self.assertRaisesRegex(ValueError, "第 [12] 条记录"):
                    storage.load_records()
                with self.assertRaises(ValueError):
                    storage.save_records([])
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_concurrent_changes_preserve_other_records(self):
        old = self.sample_record(created_at="2026-11-07T06:30:00Z")
        removed = self.sample_record(id="remove")
        storage.save_records([old, removed])

        with ThreadPoolExecutor(max_workers=8) as pool:
            adds = [
                pool.submit(add_record, "2026-11-07", "expense", amount, "饮食")
                for amount in range(1, 17)
            ]
            edit = pool.submit(update_record, old["id"], {"note": "已修改"})
            deletion = pool.submit(delete_record, removed["id"])
            added_ids = {result.result(timeout=10)["id"] for result in adds}
            self.assertTrue(edit.result(timeout=10))
            self.assertTrue(deletion.result(timeout=10))

        records = {record["id"]: record for record in storage.load_records()}
        self.assertEqual(set(records), added_ids | {old["id"]})
        self.assertEqual(records[old["id"]]["note"], "已修改")
        self.assertEqual(records[old["id"]]["created_at"], old["created_at"])

    def test_load_rejects_wrong_container_and_non_object_records(self):
        for value in ({}, None, "records", 12, [None], ["record"], [[]]):
            with self.subTest(value=value):
                original = json.dumps(value).encode("utf-8")
                self.write_raw(original)
                with self.assertRaises(ValueError):
                    storage.load_records()
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_save_rejects_wrong_container_without_changing_original(self):
        storage.save_records([self.sample_record()])
        original = self.data_file.read_bytes()
        for value in ({}, None, "records", [None], ["record"], [[]]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    storage.save_records(value)
                self.assertEqual(self.data_file.read_bytes(), original)

    def test_serialization_failure_preserves_original(self):
        storage.save_records([self.sample_record()])
        original = self.data_file.read_bytes()
        with self.assertRaises(ValueError):
            storage.save_records([self.sample_record(note={"not", "json"})])
        self.assertEqual(self.data_file.read_bytes(), original)
        self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])

    def test_non_finite_numbers_cannot_be_saved(self):
        for amount in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    storage.save_records([self.sample_record(amount=amount)])
        self.assertFalse(self.data_file.exists())

    def test_load_rejects_nonstandard_json_numbers(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                self.write_raw(('[{"amount": ' + value + "}]").encode("utf-8"))
                with self.assertRaises(ValueError):
                    storage.load_records()

    def test_save_refuses_to_overwrite_corrupt_or_wrongly_shaped_data(self):
        for original in (b"[corrupt", b"{}", b"null", b"[null]"):
            with self.subTest(original=original):
                self.write_raw(original)
                with self.assertRaises(ValueError):
                    storage.save_records([self.sample_record()])
                self.assertEqual(self.data_file.read_bytes(), original)
                self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])

    def test_replace_failure_keeps_original_and_removes_temporary_file(self):
        storage.save_records([self.sample_record()])
        original = self.data_file.read_bytes()
        with patch.object(storage.os, "replace", side_effect=PermissionError("locked")):
            with self.assertRaises(ValueError):
                storage.save_records([self.sample_record(amount=100.0)])
        self.assertEqual(self.data_file.read_bytes(), original)
        self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])

    def test_flush_to_disk_failure_keeps_original_and_cleans_up(self):
        storage.save_records([self.sample_record()])
        original = self.data_file.read_bytes()
        with patch.object(storage.os, "fsync", side_effect=OSError("disk error")):
            with self.assertRaises(ValueError):
                storage.save_records([self.sample_record(amount=100.0)])
        self.assertEqual(self.data_file.read_bytes(), original)
        self.assertEqual(list(self.data_file.parent.iterdir()), [self.data_file])

    def test_read_permission_failure_is_not_treated_as_empty_data(self):
        with patch.object(Path, "open", side_effect=PermissionError("denied")):
            with self.assertRaises(ValueError):
                storage.load_records()

    def test_storage_path_is_independent_of_working_directory(self):
        previous_directory = Path.cwd()
        try:
            os.chdir(self.directory)
            records = [self.sample_record()]
            storage.save_records(records)
            self.assertEqual(storage.load_records(), records)
        finally:
            os.chdir(previous_directory)
        self.assertTrue(self.data_file.exists())
        self.assertFalse((self.directory / "records.json").exists())

    def test_records_survive_a_new_python_process(self):
        records = [self.sample_record()]
        storage.save_records(records)
        module_directory = str(Path(storage.__file__).resolve().parent)
        script = (
            "import json, sys; from pathlib import Path; "
            "sys.path.insert(0, sys.argv[1]); import storage; "
            "storage._DATA_FILE = Path(sys.argv[2]); "
            "print(json.dumps(storage.load_records(), ensure_ascii=True))"
        )
        result = subprocess.run(
            [sys.executable, "-B", "-c", script, module_directory, str(self.data_file)],
            cwd=self.directory,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        self.assertEqual(json.loads(result.stdout), records)


if __name__ == "__main__":
    unittest.main()
