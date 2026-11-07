"""用隔离的账本走通 Streamlit 业务页面。"""

from datetime import date, timedelta
from pathlib import Path
import sys
from types import ModuleType

import pytest
from streamlit.testing.v1 import AppTest

import storage


APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture
def ledger(monkeypatch, tmp_path):
    path = tmp_path / "records.json"
    monkeypatch.setattr(storage, "_DATA_FILE", path)
    return path


def widget(widgets, label):
    return next(item for item in widgets if item.label == label)


def test_record_workflow(ledger, monkeypatch):
    monkeypatch.setitem(sys.modules, "statistics", ModuleType("statistics"))
    app = AppTest.from_file(str(APP), default_timeout=20).run()

    def nav(page):
        app.sidebar.radio[0].set_value(page).run()

    today = date.today()
    earlier = today - timedelta(days=1)

    assert not ledger.exists()
    widget(app.text_input, "备注（可选）").set_value("暂未提交")
    app.button[0].click().run()
    assert "金额必须大于 0" in app.error[0].value
    assert app.text_input[0].value == "暂未提交"
    assert not ledger.exists()

    app.number_input[0].set_value(30.0)
    app.date_input[0].set_value(today)
    app.button[0].click().run()
    assert "支出 30.00" in app.success[0].value
    assert app.number_input[0].value == 0

    widget(app.radio, "类型").set_value("income").run()
    assert "工资" in app.selectbox[0].options
    app.selectbox[0].set_value("工资")
    app.number_input[0].set_value(100.0)
    app.date_input[0].set_value(earlier)
    app.button[0].click().run()
    assert "收入 100.00" in app.success[0].value
    assert len(storage.load_records()) == 2

    app = AppTest.from_file(str(APP), default_timeout=20).run()
    nav("最近记录")
    assert app.dataframe[0].value["金额（元）"].tolist() == [30.0, 100.0]

    nav("筛选统计")
    assert [metric.value for metric in app.metric] == ["¥100.00", "¥30.00", "¥70.00", "2"]
    widget(app.selectbox, "类型").set_value("expense").run()
    widget(app.selectbox, "类别").set_value("饮食")
    widget(app.date_input, "开始日期").set_value(today)
    widget(app.date_input, "结束日期").set_value(today)
    widget(app.number_input, "最小金额").set_value(30.0)
    widget(app.number_input, "最大金额").set_value(30.0)
    app.run()
    assert [metric.value for metric in app.metric] == ["¥0.00", "¥30.00", "¥-30.00", "1"]
    widget(app.date_input, "结束日期").set_value(earlier).run()
    assert "开始日期不能晚于结束日期" in app.error[0].value
    assert not app.metric

    nav("数据图表")
    assert [metric.value for metric in app.metric] == ["¥100.00", "¥30.00", "¥70.00"]
    assert len(app.get("vega_lite_chart") or app.get("arrow_vega_lite_chart")) == 2

    nav("编辑与删除")
    assert widget(app.button, "删除记录").disabled
    app.number_input[0].set_value(35.0)
    widget(app.button, "保存修改").click().run()
    assert "已保存修改" in app.success[0].value
    assert storage.load_records()[0]["amount"] == 35.0
    app.checkbox[0].check().run()
    widget(app.button, "删除记录").click().run()
    assert "已删除记录" in app.success[0].value
    assert [record["amount"] for record in storage.load_records()] == [100.0]

    nav("导出 CSV")
    assert len(app.get("download_button")) == 1
    assert not app.error
    assert not app.exception


@pytest.mark.parametrize("payload", [b"[{", b"[{}]"])
def test_bad_ledger_blocks_editing_and_leaves_file_intact(ledger, payload):
    ledger.write_bytes(payload)
    app = AppTest.from_file(str(APP), default_timeout=20).run()
    assert "账本读取失败" in app.error[0].value
    assert not app.button
    assert not app.exception
    assert ledger.read_bytes() == payload
