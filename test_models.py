from models import create_record, validate_record

# 测试1：创建一条支出记录
record = create_record(
    date="2026-11-07",
    record_type="expense",
    amount=25.50,
    category="饮食",
    note="午餐"
)

print("创建成功：")
print(record)

# 测试2：验证合法记录
validate_record(record)
print("合法记录校验通过！")

# 测试3：测试非法金额
try:
    create_record(
        date="2026-11-07",
        record_type="expense",
        amount=0,
        category="饮食"
    )
except ValueError as e:
    print("错误测试通过：", e)

# 测试4：测试非法类别
try:
    create_record(
        date="2026-11-07",
        record_type="expense",
        amount=20,
        category="工资"
    )
except ValueError as e:
    print("类别测试通过：", e)

# 测试5：测试非法日期
try:
    create_record(
        date="2026-02-30",
        record_type="income",
        amount=100,
        category="工资"
    )
except ValueError as e:
    print("日期测试通过：", e)



# 补充测试1：金额超过两位小数
try:
    create_record(
        "2026-11-07", "expense",
        12.345, "饮食"
    )
except ValueError as e:
    print("金额精度测试通过：", e)

# 补充测试2：备注超过200个字符
try:
    create_record(
        "2026-11-07", "expense",
        10, "饮食", "测" * 201
    )
except ValueError as e:
    print("备注长度测试通过：", e)

# 补充测试3：缺少必要字段
try:
    invalid_record = record.copy()
    del invalid_record["category"]
    validate_record(invalid_record)
except ValueError as e:
    print("字段完整性测试通过：", e)

# 补充测试4：创建时间不包含时区
try:
    invalid_record = record.copy()
    invalid_record["created_at"] = "2026-11-07T14:00:00"
    validate_record(invalid_record)
except ValueError as e:
    print("时区测试通过：", e)