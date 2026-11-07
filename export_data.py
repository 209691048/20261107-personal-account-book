"""将传入的记账记录转换为可下载的 CSV。"""

import csv
from io import StringIO


_CSV_FIELDS = ("id", "date", "type", "amount", "category", "note", "created_at")


def _spreadsheet_value(value):
    if isinstance(value, str) and (
        value.startswith(("\t", "\r", "\n"))
        or value.lstrip().startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠"))
    ):
        return "'" + value
    return value


def export_csv(records: list[dict]) -> bytes:
    """按固定列顺序返回带 UTF-8 BOM 的 CSV 字节流。"""
    with StringIO(newline="") as output:
        csv.writer(output).writerow(_CSV_FIELDS)
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for record in records:
            writer.writerow(_spreadsheet_value(record.get(field, "")) for field in _CSV_FIELDS)
        return output.getvalue().encode("utf-8-sig")
