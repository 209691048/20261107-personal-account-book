# 9 编辑与删除模块
# TODO: 组员I - 按 id 修改记录字段 / 删除记录

import storage
import models

def update_record(record_id: str, updates: dict) -> bool:
    """
    按唯一 ID 修改记录
    """
    # 1. 检查 updates 是否包含非法字段（只能改这5个，不能改 id 和 created_at）
    allowed_keys = {"date", "type", "amount", "category", "note"}
    for key in updates:
        if key not in allowed_keys:
            raise ValueError(f"不允许修改字段: {key}")

    # 2. 读取所有记录
    records = storage.load_records()

    # 3. 寻找目标记录并修改
    found = False
    for i, record in enumerate(records):
        if record["id"] == record_id:
            # 合并更新，保留原有的 id 和 created_at
            records[i].update(updates)

            # 4. 校验合并后的完整记录（调用队友的 models.py）
            models.validate_record(records[i])
            found = True
            break

    # 5. 如果找到了，保存并返回 True
    if found:
        storage.save_records(records)
        return True

    # 6. 没找到返回 False
    return False


def delete_record(record_id: str) -> bool:
    """
    按唯一 ID 删除记录
    """
    # 1. 读取所有记录
    records = storage.load_records()

    # 2. 过滤掉要删除的 ID (保留不等于 record_id 的记录)
    new_records = [r for r in records if r["id"] != record_id]

    # 3. 如果长度变了，说明删除了数据
    if len(new_records) < len(records):
        storage.save_records(new_records)
        return True

    # 4. 如果长度没变，说明没找到该 ID
    return False