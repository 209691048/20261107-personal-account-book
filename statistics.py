# statistics.py
# 负责模块：7号 - 收支统计模块

def calculate_summary(records: list[dict]) -> dict:
    """计算总收入、总支出、结余和记录总数"""
    income = 0.0
    expense = 0.0
    count = len(records)

    for record in records:
        amount = float(record['amount'])
        if record['type'] == 'income':
            income += amount
        elif record['type'] == 'expense':
            expense += amount
        else:
            raise ValueError(f"非法收支类型: {record['type']}，只能是 income 或 expense")

    balance = round(income - expense, 2)
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": balance,
        "count": count
    }