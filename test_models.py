from uuid import UUID

import pytest

from models import create_record, validate_record


def expense(**changes):
    fields = {
        "date": "2026-11-07",
        "record_type": "expense",
        "amount": 25.50,
        "category": "饮食",
        "note": "午餐",
    }
    return create_record(**{**fields, **changes})


def test_creates_a_valid_record():
    record = expense()
    assert UUID(record["id"]).version == 4
    assert record["amount"] == 25.50
    assert record["type"] == "expense"
    assert validate_record(record) is None


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"amount": 0}, "金额必须大于 0"),
        ({"category": "工资"}, "类别与收支类型不匹配"),
        ({"date": "2026-02-30"}, "日期无效"),
        ({"amount": 12.345}, "最多保留两位小数"),
        ({"amount": 10**400}, "金额超出可保存范围"),
        ({"note": "测" * 201}, "备注不能超过200个字符"),
    ],
)
def test_create_record_rejects_invalid_input(fields, message):
    with pytest.raises(ValueError, match=message):
        expense(**fields)


def test_validate_record_requires_all_fields():
    record = expense()
    del record["category"]
    with pytest.raises(ValueError, match="记录字段不完整"):
        validate_record(record)


def test_validate_record_requires_timezone_and_accepts_utc_z():
    record = expense()
    record["created_at"] = "2026-11-07T14:00:00"
    with pytest.raises(ValueError, match="带时区"):
        validate_record(record)
    record["created_at"] += "Z"
    assert validate_record(record) is None
