"""按记录 ID 修改或删除账本条目。"""

import models
import storage


def update_record(record_id: str, updates: dict) -> bool:
    """校验并保存目标记录。找不到目标时返回 False。"""
    if not isinstance(updates, dict):
        raise ValueError("修改内容必须是字典")
    allowed_keys = {"date", "type", "amount", "category", "note"}
    for key in updates:
        if key not in allowed_keys:
            raise ValueError(f"不允许修改字段: {key}")

    with storage._RECORDS_LOCK:
        records = storage.load_records()
        for index, record in enumerate(records):
            if record["id"] == record_id:
                updated = {**record, **updates}
                models.validate_record(updated)
                records[index] = updated
                storage.save_records(records)
                return True
    return False


def delete_record(record_id: str) -> bool:
    """删除目标记录。找不到目标时返回 False。"""
    with storage._RECORDS_LOCK:
        records = storage.load_records()
        remaining = [record for record in records if record["id"] != record_id]
        if len(remaining) < len(records):
            storage.save_records(remaining)
            return True
    return False
