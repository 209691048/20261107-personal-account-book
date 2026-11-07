"""兼容原有的账本统计接口。业务代码使用 account_statistics。"""

from account_statistics import calculate_summary, category_totals

__all__ = ["calculate_summary", "category_totals"]
