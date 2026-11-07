"""新增收入或支出记录的固定业务入口。"""

from __future__ import annotations

from models import create_record
from storage import _RECORDS_LOCK


def _load_records() -> list[dict]:
    """延迟导入团队唯一存储入口，便于独立测试且不复制 storage.py。"""
    from storage import load_records

    return load_records()


def _save_records(records: list[dict]) -> None:
    """延迟导入团队唯一存储入口，保存失败时让异常向上抛出。"""
    from storage import save_records

    save_records(records)


def add_record(
    date: str,
    record_type: str,
    amount: float,
    category: str,
    note: str = "",
) -> dict:
    """校验输入，将新记录追加到本地数据并返回刚添加的完整记录。

    执行顺序严格为：create_record -> load_records -> 添加 -> save_records。
    任何校验或保存异常都会向上抛出，不会静默吞掉。
    """
    record = create_record(date, record_type, amount, category, note)

    with _RECORDS_LOCK:
        records = _load_records()
        if not isinstance(records, list):
            raise ValueError("load_records() 必须返回记录列表")

        _save_records([*records, record])
    return record
