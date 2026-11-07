# 6 条件筛选模块
from datetime import date, datetime
from math import isfinite


def filter_records(
    records: list[dict],
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    record_type: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
) -> list[dict]:
    """组合筛选有效记录，区间含边界，按日期和创建时间倒序返回新列表。"""
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{name} 必须是 YYYY-MM-DD 格式的有效日期")
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                raise ValueError(f"{name} 必须是 YYYY-MM-DD 格式的有效日期") from None
            if parsed.isoformat() != value:
                raise ValueError(f"{name} 必须是 YYYY-MM-DD 格式的有效日期")

    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("开始日期不能晚于结束日期")
    if category is not None and not isinstance(category, str):
        raise ValueError("category 必须是字符串")
    if record_type is not None and record_type not in ("income", "expense"):
        raise ValueError("record_type 必须是 income 或 expense")
    for name, value in (("min_amount", min_amount), ("max_amount", max_amount)):
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (isinstance(value, float) and not isfinite(value))
        ):
            raise ValueError(f"{name} 必须是有限数字")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise ValueError("最低金额不能高于最高金额")

    selected = [
        record
        for record in records
        if (start_date is None or record["date"] >= start_date)
        and (end_date is None or record["date"] <= end_date)
        and (category is None or record["category"] == category)
        and (record_type is None or record["type"] == record_type)
        and (min_amount is None or record["amount"] >= min_amount)
        and (max_amount is None or record["amount"] <= max_amount)
    ]
    return sorted(
        selected,
        key=lambda record: (
            record["date"],
            datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")),
        ),
        reverse=True,
    )
