# -*- coding: utf-8 -*-
"""8 号模块：charts.py —— 数据图表。

职责
----
在 Streamlit 页面中展示两张图：

1. 收入 / 支出对比（柱状图，数据来自 ``statistics.calculate_summary``）；
2. 支出类别分布（横向条形图，数据来自 ``statistics.category_totals``）。

约束（见《个人记账本开发规范 v1.0》）
------------------------------------
- 对外只暴露 ``render_charts(records) -> None``；
- 不读写 ``data/records.json``，不修改传入的 ``records``；
- 空数据只提示，不抛异常；
- 统计口径全部复用 ``statistics.py``，不在本模块重复实现。

依赖：``streamlit``、``pandas``、``altair``（后两者随 Streamlit 安装）。
"""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# 视觉常量
#
# 收入用蓝、支出用红，两张图沿用同一套语义；分类支出是「一个系列」，
# 因此所有柱子用同一个色相，不按金额深浅上色（避免用颜色重复编码长度）。
# ---------------------------------------------------------------------------
INCOME_COLOR = "#2a78d6"
EXPENSE_COLOR = "#e34948"
CATEGORY_COLOR = "#2a78d6"

INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

_SUMMARY_KEYS = ("income", "expense", "balance", "count")


# ---------------------------------------------------------------------------
# 数据准备：只调用 statistics.py，不自己算统计口径
# ---------------------------------------------------------------------------
def _statistics_api():
    """延迟导入统计模块。

    延迟导入的原因：charts 依赖 7 号模块，但开发/测试阶段 ``statistics.py``
    可能还是占位文件。这样 charts 本身仍可导入，真正渲染时再给出明确错误，
    而不是在 ``import charts`` 阶段就抛一个难以定位的 ImportError。
    """
    try:
        from statistics import calculate_summary, category_totals
    except ImportError as exc:  # 统计模块尚未实现或尚未合并
        raise RuntimeError(
            "charts 依赖 statistics.py 的 calculate_summary() 和 "
            "category_totals()，请先合并 7 号统计模块"
        ) from exc
    return calculate_summary, category_totals


def _as_record_list(records: Any) -> list[dict]:
    """把入参统一成列表，且不复制、不修改记录内容。"""
    if records is None:
        return []
    if isinstance(records, dict):
        return [records]
    try:
        return list(records)
    except TypeError as exc:
        raise ValueError("records 必须是记录字典组成的列表") from exc


def _prepare_summary(records: list[dict]) -> dict:
    """调用 statistics.calculate_summary，并校验固定返回结构。"""
    calculate_summary, _ = _statistics_api()
    summary = calculate_summary(records)

    if not isinstance(summary, dict):
        raise RuntimeError("statistics.calculate_summary 必须返回 dict")
    missing = [key for key in _SUMMARY_KEYS if key not in summary]
    if missing:
        raise RuntimeError(
            "statistics.calculate_summary 返回值缺少字段：" + "、".join(missing)
        )

    try:
        return {
            "income": float(summary["income"]),
            "expense": float(summary["expense"]),
            "balance": float(summary["balance"]),
            "count": int(summary["count"]),
        }
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "statistics.calculate_summary 返回的金额或条数不是数字"
        ) from exc


def _prepare_category_data(records: list[dict]) -> pd.DataFrame:
    """调用 statistics.category_totals，返回按金额降序排列的 DataFrame。

    - 只保留金额大于 0 的类别；
    - 金额相同按类别名排序，保证每次渲染顺序稳定；
    - 空结果返回带列名的空表，方便调用方用 ``.empty`` 判断。
    """
    _, category_totals = _statistics_api()
    totals = category_totals(records, "expense")

    if not isinstance(totals, dict):
        raise RuntimeError("statistics.category_totals 必须返回 dict[str, float]")

    rows: list[tuple[str, float]] = []
    for category, amount in totals.items():
        try:
            value = float(amount)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"statistics.category_totals 中类别 {category!r} 的金额不是数字"
            ) from exc
        if value > 0:
            rows.append((str(category), round(value, 2)))

    rows.sort(key=lambda item: (-item[1], item[0]))
    return pd.DataFrame(rows, columns=["category", "amount"])


def _format_money(value: float) -> str:
    """金额显示：1234.5 -> ¥1,234.50；负数把负号放在货币符号前。"""
    number = float(value)
    sign = "-" if number < 0 else ""
    return f"{sign}¥{abs(number):,.2f}"


# ---------------------------------------------------------------------------
# 图表构建（Altair；由 Streamlit 渲染，自适应容器宽度）
# ---------------------------------------------------------------------------
def _comparison_chart(summary: dict) -> alt.LayerChart:
    """收入 / 支出对比柱状图。

    只有两个并列的柱子，横轴标签已经说明身份，因此不再放重复的图例；
    柱子顶部直接标金额，满足「不靠颜色单独编码」的要求。
    """
    data = pd.DataFrame(
        {
            "kind": ["收入", "支出"],
            "amount": [max(summary["income"], 0.0), max(summary["expense"], 0.0)],
            "color": [INCOME_COLOR, EXPENSE_COLOR],
        }
    )
    # 金额直接带 ¥ 标在柱顶，纵轴不再放会被竖排的中文标题。
    data["label"] = data["amount"].map(_format_money)
    peak = max(float(data["amount"].max()), 1.0)

    base = alt.Chart(data).encode(
        x=alt.X(
            "kind:N",
            title=None,
            sort=["收入", "支出"],
            axis=alt.Axis(
                labelAngle=0,
                labelColor=INK_SECONDARY,
                labelFontSize=12,
                domainColor=AXIS,
                ticks=False,
            ),
        ),
        y=alt.Y(
            "amount:Q",
            title=None,
            scale=alt.Scale(domain=[0, peak * 1.18], zero=True),
            axis=alt.Axis(
                labelColor=MUTED,
                gridColor=GRID,
                domainColor=AXIS,
                tickColor=AXIS,
                format=",.0f",
                tickCount=6,
            ),
        ),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[
            alt.Tooltip("kind:N", title="类型"),
            alt.Tooltip("amount:Q", title="金额（元）", format=",.2f"),
        ],
    )

    bars = base.mark_bar(size=24)
    labels = base.mark_text(dy=-10, fontSize=12).encode(
        text=alt.Text("label:N"),
        color=alt.value(INK_SECONDARY),
    )
    return (bars + labels).properties(height=250).configure_view(strokeWidth=0)


def _category_chart(frame: pd.DataFrame) -> alt.LayerChart:
    """支出类别横向条形图。

    中文类别名放在纵轴，避免横轴标签倾斜；条形从零开始、按金额降序，
    金额标在条尾。只用一种颜色，因为这里只有「支出金额」一个系列。
    """
    data = frame.copy()
    data["label"] = data["amount"].map(_format_money)
    peak = max(float(data["amount"].max()), 1.0)

    base = alt.Chart(data).encode(
        y=alt.Y(
            "category:N",
            title=None,
            sort="-x",
            axis=alt.Axis(
                labelColor=INK_SECONDARY,
                labelFontSize=12,
                domainColor=AXIS,
                ticks=False,
            ),
        ),
        x=alt.X(
            "amount:Q",
            title=None,
            scale=alt.Scale(domain=[0, peak * 1.22], zero=True),
            axis=alt.Axis(
                labelColor=MUTED,
                gridColor=GRID,
                domainColor=AXIS,
                tickColor=AXIS,
                format=",.0f",
                tickCount=6,
            ),
        ),
        tooltip=[
            alt.Tooltip("category:N", title="类别"),
            alt.Tooltip("amount:Q", title="金额（元）", format=",.2f"),
        ],
    )

    bars = base.mark_bar(size=18, color=CATEGORY_COLOR)
    labels = base.mark_text(align="left", dx=6, fontSize=11).encode(
        text=alt.Text("label:N"),
        color=alt.value(INK_SECONDARY),
    )
    height = max(180, 44 * len(data))
    return (bars + labels).properties(height=height).configure_view(strokeWidth=0)


# ---------------------------------------------------------------------------
# 唯一公开接口
# ---------------------------------------------------------------------------
def render_charts(records: list[dict]) -> None:
    """在当前 Streamlit 页面渲染收支图表。

    参数
    ----
    records : list[dict]
        记录列表（``storage.load_records()`` 的返回值）。只读，不修改。

    返回
    ----
    None
        所有内容通过 ``st`` 组件输出。

    空记录、只有收入没有支出等情况都只显示提示，不会抛异常。
    """
    record_list = _as_record_list(records)

    # 页面标题由 app.py 的 page_charts() 负责，这里不再重复输出。
    if not record_list:
        st.info("暂无记账数据。先添加一笔收入或支出，这里会自动生成图表。")
        return

    summary = _prepare_summary(record_list)
    category_frame = _prepare_category_data(record_list)

    income_col, expense_col, balance_col = st.columns(3)
    income_col.metric("总收入", _format_money(summary["income"]))
    expense_col.metric("总支出", _format_money(summary["expense"]))
    balance_col.metric("结余", _format_money(summary["balance"]))

    st.markdown("**收入与支出对比**")
    st.altair_chart(_comparison_chart(summary), use_container_width=True)

    st.markdown("**支出类别分布**")
    if category_frame.empty:
        st.info("暂无支出记录，添加一笔支出后这里会显示分类图表。")
        return

    st.altair_chart(_category_chart(category_frame), use_container_width=True)

    # 表格视图：图表之外也能逐项读到数值（打印、色觉障碍、读屏都更友好）。
    with st.expander("查看分类数据表"):
        table = category_frame.copy()
        table["amount"] = table["amount"].map(_format_money)
        table.columns = ["类别", "金额"]
        st.dataframe(table, hide_index=True, use_container_width=True)
