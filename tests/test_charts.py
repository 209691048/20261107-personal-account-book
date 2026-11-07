# -*- coding: utf-8 -*-
"""charts.py 的单元测试。

测试不依赖真实 Streamlit 运行时：
- 用假的 statistics 模块固定统计口径；
- 用 FakeStreamlit 记录 render_charts 调用了哪些组件。

重点覆盖：空数据、只有收入 / 只有支出、排序与过滤、返回结构校验、
以及「不修改传入记录」。
"""

import copy
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

import altair as alt
import pandas as pd

# 允许直接运行 `pytest tests/test_charts.py` 时也能找到仓库根目录的 charts.py。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import charts  # noqa: E402


# ---------------------------------------------------------------------------
# 测试数据与 statistics 替身
# ---------------------------------------------------------------------------
def make_record(record_id, date, record_type, amount, category, note=""):
    return {
        "id": record_id,
        "date": date,
        "type": record_type,
        "amount": amount,
        "category": category,
        "note": note,
        "created_at": date + "T06:30:00+00:00",
    }


RECORDS = [
    make_record("a", "2026-11-01", "income", 100.0, "工资"),
    make_record("b", "2026-11-02", "expense", 30.0, "饮食"),
]
INCOME_ONLY = [make_record("c", "2026-11-03", "income", 200.0, "兼职")]
EXPENSE_ONLY = [make_record("d", "2026-11-04", "expense", 12.5, "交通")]


def fake_calculate_summary(records):
    income = sum(float(r["amount"]) for r in records if r["type"] == "income")
    expense = sum(float(r["amount"]) for r in records if r["type"] == "expense")
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "balance": round(income - expense, 2),
        "count": len(records),
    }


def fake_category_totals(records, record_type="expense"):
    totals = {}
    for record in records:
        if record["type"] != record_type:
            continue
        category = record["category"]
        totals[category] = round(
            totals.get(category, 0.0) + float(record["amount"]), 2
        )
    return totals


# ---------------------------------------------------------------------------
# Fake Streamlit：记录组件调用，不启动真实页面
# ---------------------------------------------------------------------------
class FakeColumn:
    def __init__(self, sink):
        self._sink = sink

    def metric(self, label, value, **kwargs):
        self._sink.append(("metric", label, value))


class FakeExpander:
    def __init__(self, sink):
        self._sink = sink

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(self):
        self.calls = []

    def subheader(self, text, **kwargs):
        self.calls.append(("subheader", text))

    def info(self, text, **kwargs):
        self.calls.append(("info", text))

    def markdown(self, text, **kwargs):
        self.calls.append(("markdown", text))

    def columns(self, count):
        self.calls.append(("columns", count))
        return [FakeColumn(self.calls) for _ in range(count)]

    def altair_chart(self, chart, **kwargs):
        self.calls.append(("altair_chart", chart))

    def expander(self, text, **kwargs):
        self.calls.append(("expander", text))
        return FakeExpander(self.calls)

    def dataframe(self, data, **kwargs):
        self.calls.append(("dataframe", data))


class ChartsTestCase(unittest.TestCase):
    def setUp(self):
        stub = types.ModuleType("statistics")
        stub.calculate_summary = fake_calculate_summary
        stub.category_totals = fake_category_totals
        self.stub = stub
        patcher = mock.patch.dict(sys.modules, {"statistics": stub})
        patcher.start()
        self.addCleanup(patcher.stop)

    def render(self, records):
        fake = FakeStreamlit()
        with mock.patch.object(charts, "st", fake):
            result = charts.render_charts(records)
        return fake, result

    # ---------------- render_charts：空数据与边界 ----------------
    def test_empty_records_only_shows_hint(self):
        fake, result = self.render([])
        self.assertIsNone(result)
        infos = [call[1] for call in fake.calls if call[0] == "info"]
        self.assertEqual(len(infos), 1)
        self.assertIn("暂无记账数据", infos[0])
        self.assertEqual(
            len([c for c in fake.calls if c[0] == "altair_chart"]), 0
        )
        self.assertEqual(len([c for c in fake.calls if c[0] == "metric"]), 0)

    def test_none_is_treated_as_empty(self):
        fake, _ = self.render(None)
        self.assertEqual(len([c for c in fake.calls if c[0] == "info"]), 1)

    def test_single_dict_is_accepted(self):
        fake, _ = self.render(RECORDS[0])
        metrics = [(c[1], c[2]) for c in fake.calls if c[0] == "metric"]
        self.assertEqual(metrics[0], ("总收入", "¥100.00"))

    def test_only_income_still_renders_comparison(self):
        fake, _ = self.render(INCOME_ONLY)
        charts_rendered = [c for c in fake.calls if c[0] == "altair_chart"]
        self.assertEqual(len(charts_rendered), 1)  # 只有收支对比图
        infos = [c[1] for c in fake.calls if c[0] == "info"]
        self.assertTrue(any("暂无支出记录" in text for text in infos))
        self.assertEqual(len([c for c in fake.calls if c[0] == "dataframe"]), 0)

    def test_records_are_not_mutated(self):
        records = copy.deepcopy(RECORDS)
        before = copy.deepcopy(records)
        self.render(records)
        self.assertEqual(records, before)

    # ---------------- 指标与图表数量 ----------------
    def test_metrics_use_statistics_summary(self):
        fake, _ = self.render(RECORDS)
        metrics = [(c[1], c[2]) for c in fake.calls if c[0] == "metric"]
        self.assertEqual(
            metrics,
            [
                ("总收入", "¥100.00"),
                ("总支出", "¥30.00"),
                ("结余", "¥70.00"),
            ],
        )

    def test_two_charts_and_table_are_rendered(self):
        fake, _ = self.render(RECORDS)
        chart_calls = [c[1] for c in fake.calls if c[0] == "altair_chart"]
        self.assertEqual(len(chart_calls), 2)
        for chart in chart_calls:
            # 柱子 + 数值标签是分层图，返回 LayerChart，而不是单层 Chart。
            self.assertIsInstance(chart, alt.LayerChart)
            self.assertIn("layer", chart.to_dict())

        tables = [c[1] for c in fake.calls if c[0] == "dataframe"]
        self.assertEqual(len(tables), 1)
        self.assertEqual(list(tables[0].columns), ["类别", "金额"])

    # ---------------- 数据准备：排序、过滤、结构校验 ----------------
    def test_category_data_is_sorted_and_zero_filtered(self):
        self.stub.category_totals = lambda records, record_type="expense": {
            "饮食": 10.0,
            "交通": 30.0,
            "其他": 0.0,
        }
        frame = charts._prepare_category_data(RECORDS)
        self.assertEqual(
            frame.to_dict("records"),
            [
                {"category": "交通", "amount": 30.0},
                {"category": "饮食", "amount": 10.0},
            ],
        )

    def test_category_totals_receives_expense_type(self):
        seen = []

        def spy(records, record_type="expense"):
            seen.append(record_type)
            return {}

        self.stub.category_totals = spy
        charts._prepare_category_data(RECORDS)
        self.assertEqual(seen, ["expense"])

    def test_empty_category_frame_keeps_columns(self):
        self.stub.category_totals = lambda records, record_type="expense": {}
        frame = charts._prepare_category_data(RECORDS)
        self.assertTrue(frame.empty)
        self.assertEqual(list(frame.columns), ["category", "amount"])

    def test_summary_missing_field_raises(self):
        self.stub.calculate_summary = lambda records: {"income": 1.0}
        with self.assertRaises(RuntimeError) as caught:
            charts._prepare_summary(RECORDS)
        self.assertIn("缺少字段", str(caught.exception))

    def test_summary_non_numeric_raises(self):
        self.stub.calculate_summary = lambda records: {
            "income": "一百",
            "expense": 0.0,
            "balance": 0.0,
            "count": 1,
        }
        with self.assertRaises(RuntimeError):
            charts._prepare_summary(RECORDS)

    def test_missing_statistics_module_raises_clear_error(self):
        empty_module = types.ModuleType("statistics")
        with mock.patch.dict(sys.modules, {"statistics": empty_module}):
            with self.assertRaises(RuntimeError) as caught:
                charts._prepare_summary([])
        self.assertIn("statistics.py", str(caught.exception))

    # ---------------- 小工具 ----------------
    def test_format_money(self):
        self.assertEqual(charts._format_money(1234.5), "¥1,234.50")
        self.assertEqual(charts._format_money(0), "¥0.00")
        self.assertEqual(charts._format_money(-12.3), "-¥12.30")

    def test_invalid_records_argument_raises(self):
        with self.assertRaises(ValueError):
            charts._as_record_list(123)

    # ---------------- 图表规格 ----------------
    def test_comparison_chart_uses_bar_and_labels(self):
        chart = charts._comparison_chart(
            {"income": 100.0, "expense": 30.0, "balance": 70.0, "count": 2}
        )
        spec = chart.to_dict()
        self.assertEqual(spec["layer"][0]["mark"]["type"], "bar")
        self.assertEqual(spec["layer"][0]["encoding"]["x"]["sort"], ["收入", "支出"])

    def test_category_chart_sorts_by_amount_desc(self):
        frame = pd.DataFrame(
            [("饮食", 10.0), ("交通", 30.0)], columns=["category", "amount"]
        )
        spec = charts._category_chart(frame).to_dict()
        self.assertEqual(spec["layer"][0]["encoding"]["y"]["sort"], "-x")
        self.assertEqual(
            spec["layer"][0]["mark"]["color"], charts.CATEGORY_COLOR
        )


if __name__ == "__main__":
    unittest.main()
