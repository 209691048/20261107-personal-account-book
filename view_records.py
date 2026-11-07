# 5 记录查看模块
from datetime import datetime


def get_recent_records(records: list[dict], limit: int = 10) -> list[dict]:
    """返回按发生日期和创建时间倒序排列的最近记录。"""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit 必须是非负整数")

    recent = sorted(
        records,
        key=lambda record: (
            record["date"],
            datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
        ),
        reverse=True,
    )
    return recent[:limit]
