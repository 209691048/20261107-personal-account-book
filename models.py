
"""
个人记账本 - 数据模型与校验模块 models.py

主要功能：
1. 统一定义收入和支出的类别
2. 创建新的记账记录
3. 检查记录数据是否合法

本模块不负责文件读写，也不负责界面显示。
"""

# uuid：用于生成全球唯一标识符，避免不同记录出现相同 ID
import uuid

# datetime：用于处理日期和时间
from datetime import datetime

# Decimal：用于精确检查金额的小数位数，避免浮点数精度问题
from decimal import Decimal, InvalidOperation
from math import isfinite


# ==================================================
# 一、定义收入和支出的类别常量
# ==================================================

# 支出类别：统一由 models.py 定义，其他模块直接导入使用
EXPENSE_CATEGORIES = [
    "饮食", "交通", "购物", "娱乐",
    "住房", "医疗", "学习", "其他"
]

# 收入类别
INCOME_CATEGORIES = [
    "工资", "兼职", "奖学金", "奖金", "其他"
]

# 每条记录必须包含的字段
# 使用集合 set 方便统一检查字段是否完整，是否存在多余字段
REQUIRED_FIELDS = {
    "id",
    "date",
    "type",
    "amount",
    "category",
    "note",
    "created_at"
}


# ==================================================
# 二、创建记账记录
# ==================================================

def create_record(
    date: str,
    record_type: str,
    amount: float,
    category: str,
    note: str = ""
) -> dict:
    """
    创建一条完整的收入或支出记录。

    参数：
        date：记账日期，格式为 YYYY-MM-DD
        record_type：收支类型，income 或 expense
        amount：金额
        category：收支类别
        note：备注，默认为空字符串

    返回：
        包含全部字段的字典
    """

    # uuid.uuid4().hex 自动生成32位十六进制字符串
    # 每条新记录都有自己的唯一 ID，方便后续修改和删除
    record_id = uuid.uuid4().hex

    # 获取当前本地时间，并自动附带时区信息
    # isoformat() 将时间转换为 ISO 8601 标准字符串
    created_time = datetime.now().astimezone().isoformat()

    # 使用字典保存一条完整的记账记录
    # 字段名称必须与团队统一数据规范保持一致
    record = {
        "id": record_id,
        "date": date,
        "type": record_type,
        "amount": amount,
        "category": category,
        "note": note,
        "created_at": created_time
    }

    # 创建完成后立即进行数据校验
    # 如果发现错误，validate_record 会抛出 ValueError
    validate_record(record)

    # 统一将金额转换为 float 类型，保证 JSON 中保存的是数字
    record["amount"] = float(record["amount"])

    # 返回创建完成的完整记录
    return record


# ==================================================
# 三、校验记账记录
# ==================================================

def validate_record(record: dict) -> None:
    """
    检查记账记录是否符合统一的数据规范。

    参数：
        record：需要校验的记录字典

    返回：
        合法时返回 None

    异常：
        不合法时抛出 ValueError，并说明错误原因
    """

    # 1. 检查数据类型
    # 记录必须使用字典保存，不能传入字符串或列表
    if not isinstance(record, dict):
        raise ValueError("记录必须是字典类型")

    # 2. 检查字段完整性
    # 比较实际字段与规定字段，防止缺少字段或出现多余字段
    if set(record.keys()) != REQUIRED_FIELDS:
        raise ValueError("记录字段不完整或包含多余字段")

    # 3. 检查唯一 ID
    # ID 必须是非空字符串
    if not isinstance(record["id"], str) or not record["id"].strip():
        raise ValueError("记录 ID 必须是非空字符串")

    # 4. 检查日期
    date = record["date"]

    if not isinstance(date, str):
        raise ValueError("日期必须是字符串")

    try:
        # strptime() 按指定格式解析日期
        # 不仅检查格式，还能识别 2 月 30 日等无效日期
        parsed_date = datetime.strptime(date, "%Y-%m-%d")

        # 再次格式化并比较，确保日期严格符合 YYYY-MM-DD
        if parsed_date.date().isoformat() != date:
            raise ValueError("日期格式必须为 YYYY-MM-DD")

    except ValueError:
        raise ValueError("日期无效，请使用 YYYY-MM-DD 格式")

    # 5. 检查收支类型
    # 只允许 income（收入）和 expense（支出）
    record_type = record["type"]

    if record_type not in ("income", "expense"):
        raise ValueError("收支类型只能是 income 或 expense")

    # 6. 检查金额
    amount = record["amount"]

    # bool 是 int 的子类，因此需要单独排除 True 和 False
    # 金额只允许整数或浮点数
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("金额必须是数字")

    try:
        # Decimal(str()) 将金额转换为十进制形式
        # 比直接使用 float 更适合检查金额的小数位数
        decimal_amount = Decimal(str(amount))

    except InvalidOperation:
        raise ValueError("金额格式不正确")

    # 检查金额是否为有限数字，并且必须大于 0
    # 排除 0、负数、NaN 和无穷大
    if not decimal_amount.is_finite() or decimal_amount <= 0:
        raise ValueError("金额必须大于 0")
    if not isfinite(float(decimal_amount)):
        raise ValueError("金额超出可保存范围")

    # Decimal 的 exponent 表示小数位数的负值
    # 例如 12.50 的 exponent 为 -2
    # 小于 -2 说明超过两位小数
    if decimal_amount.as_tuple().exponent < -2:
        raise ValueError("金额最多保留两位小数")

    # 7. 检查收支类别
    category = record["category"]

    if not isinstance(category, str):
        raise ValueError("类别必须是字符串")

    # 根据收支类型选择对应的合法类别
    # 防止出现支出记录选择工资类别等错误
    if record_type == "expense":
        valid_categories = EXPENSE_CATEGORIES
    else:
        valid_categories = INCOME_CATEGORIES

    # 检查类别是否存在于对应类别列表中
    if category not in valid_categories:
        raise ValueError("所选类别与收支类型不匹配")

    # 8. 检查备注
    note = record["note"]

    if not isinstance(note, str):
        raise ValueError("备注必须是字符串")

    # 备注允许为空，但最长不能超过200个字符
    if len(note) > 200:
        raise ValueError("备注不能超过200个字符")

    # 9. 检查创建时间
    created_at = record["created_at"]

    if not isinstance(created_at, str):
        raise ValueError("创建时间必须是字符串")

    try:
        # fromisoformat() 将 ISO 8601 字符串解析为时间对象
        if created_at.endswith("Z"):
            created_at = created_at[:-1] + "+00:00"
        parsed_time = datetime.fromisoformat(created_at)

        # 检查时间是否包含时区信息
        # 没有时区的时间不符合团队规范
        if parsed_time.tzinfo is None or parsed_time.utcoffset() is None:
            raise ValueError("创建时间必须包含时区信息")

    except ValueError:
        raise ValueError(
            "创建时间格式无效，必须使用带时区的 ISO 8601 格式"
        )

    # 所有检查通过，不需要返回具体内容
    # Python 函数默认返回 None
