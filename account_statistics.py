"""计算账本的收支与分类统计。"""

from decimal import Decimal, InvalidOperation, localcontext
from math import isfinite

_PRECISION = 330  # 覆盖有限 float 的整数位数及分位。


def _amount(record: dict) -> Decimal:
    try:
        amount = Decimal(str(record["amount"]))
    except InvalidOperation as exc:
        raise ValueError("统计金额必须是数字") from exc
    if not amount.is_finite():
        raise ValueError("统计金额必须是有限数字")
    return amount


def _money(amount: Decimal) -> float:
    rounded = float(round(amount, 2))
    if not isfinite(rounded):
        raise ValueError("统计金额超出可显示范围")
    return rounded

def calculate_summary(records: list[dict]) -> dict:
    """计算总收入、总支出、结余和记录总数"""
    totals = {"income": Decimal(0), "expense": Decimal(0)}
    with localcontext() as context:
        context.prec = _PRECISION
        for record in records:
            record_type = record["type"]
            if record_type not in ("income", "expense"):
                raise ValueError(f"非法收支类型: {record_type}，只能是 income 或 expense")
            totals[record_type] += _amount(record)
        return {
            "income": _money(totals["income"]),
            "expense": _money(totals["expense"]),
            "balance": _money(totals["income"] - totals["expense"]),
            "count": len(records),
        }


def category_totals(records: list[dict], record_type: str = "expense") -> dict[str, float]:
    """汇总指定收支类型下各分类的金额。"""
    if record_type not in ("income", "expense"):
        raise ValueError(f"record_type 只能是 'income' 或 'expense'，收到: {record_type}")

    totals: dict[str, Decimal] = {}
    with localcontext() as context:
        context.prec = _PRECISION
        for record in records:
            if record["type"] == record_type:
                category = record["category"]
                totals[category] = totals.get(category, Decimal(0)) + _amount(record)
        return {category: _money(amount) for category, amount in totals.items()}
