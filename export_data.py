"""将传入的记账记录转换为可下载的 CSV。"""

import csv
from io import StringIO


_CSV_FIELDS = ("id", "date", "type", "amount", "category", "note", "created_at")


def export_csv(records: list[dict]) -> bytes:
    """按固定列顺序返回带 UTF-8 BOM 的 CSV 字节流。"""
    with StringIO(newline="") as output:
        writer = csv.DictWriter(output, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        return output.getvalue().encode("utf-8-sig")
