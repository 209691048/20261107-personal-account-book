import pytest

from account_statistics import calculate_summary, category_totals

def test_empty_records():
    res = calculate_summary([])
    assert res == {"income":0.0,"expense":0.0,"balance":0.0,"count":0}

def test_normal_summary():
    recs = [
        {"type":"income","amount":5000.0,"category":"工资"},
        {"type":"expense","amount":123.45,"category":"饮食"},
        {"type":"expense","amount":200.55,"category":"交通"},
    ]
    s = calculate_summary(recs)
    assert abs(s["income"] - 5000.0) < 0.01
    assert abs(s["expense"] - 324.0) < 0.01
    assert abs(s["balance"] - 4676.0) < 0.01
    assert s["count"] == 3

def test_category_total_expense():
    recs = [
        {"type":"expense","category":"饮食","amount":10.1},
        {"type":"expense","category":"饮食","amount":20.2},
        {"type":"income","category":"工资","amount":1000}
    ]
    cat_exp = category_totals(recs,"expense")
    assert abs(cat_exp["饮食"] - 30.3) < 0.01
    cat_inc = category_totals(recs,"income")
    assert abs(cat_inc["工资"] - 1000.0) < 0.01

def test_category_bad_param():
    """验证传入非法record_type会抛出ValueError"""
    with pytest.raises(ValueError, match="record_type"):
        category_totals([], record_type="hello")


def test_balance_keeps_cents_after_large_amounts_cancel():
    records = [
        {"type": "income", "amount": 10_000_000_000_000_000, "category": "工资"},
        {"type": "income", "amount": 0.01, "category": "其他"},
        {"type": "expense", "amount": 10_000_000_000_000_000, "category": "其他"},
    ]
    assert calculate_summary(records)["balance"] == 0.01


if __name__ == "__main__":
    test_empty_records()
    print("✅ test_empty_records 通过")

    test_normal_summary()
    print("✅ test_normal_summary 通过")

    test_category_total_expense()
    print("✅ test_category_total_expense 通过")

    # 手动执行异常用例
    test_category_bad_param()
    print("✅ test_category_bad_param 通过")

    print("\n===== 全部4项测试逻辑验证完成 =====")
