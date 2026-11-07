"""拾光账本的 Streamlit 业务入口。"""

from datetime import date

import streamlit as st
import ledger_ui as ui

from account_statistics import calculate_summary
from add_record import add_record
from charts import render_charts
from export_data import export_csv
from filter_records import filter_records
from manage_records import delete_record, update_record
from models import EXPENSE_CATEGORIES, INCOME_CATEGORIES
from storage import load_records
from view_records import get_recent_records


_TYPE_LABELS = {"expense": "支出", "income": "收入"}
_CATEGORIES = {"expense": EXPENSE_CATEGORIES, "income": INCOME_CATEGORIES}
_NAV_LABELS = {
    "收支总览": "▦   收支总览",
    "新增记账": "＋   新增记账",
    "最近记录": "≡   最近记录",
    "筛选统计": "⌕   筛选统计",
    "数据图表": "▥   数据图表",
    "编辑与删除": "✎   编辑与删除",
    "导出 CSV": "↧   导出 CSV",
}


def _navigate(page):
    st.session_state["ledger_page"] = page


def _record_fields(record_type, record):
    """在新增和编辑表单中使用相同的字段和控件。"""
    categories = _CATEGORIES[record_type]
    category = record.get("category")
    left, right = st.columns(2)
    amount = left.number_input(
        "金额（元）", min_value=0.0, value=float(record.get("amount", 0)),
        step=0.01, format="%.2f",
    )
    record_date = left.date_input("日期", value=date.fromisoformat(record["date"]))
    category = right.selectbox(
        "类别", categories, index=categories.index(category) if category in categories else 0,
    )
    note = right.text_input("备注（可选）", value=record.get("note", ""), max_chars=200)
    return {
        "date": record_date.isoformat(),
        "type": record_type,
        "amount": amount,
        "category": category,
        "note": note,
    }


def _record_table(records):
    rows = [
        {
            "日期": record["date"],
            "类型": _TYPE_LABELS[record["type"]],
            "类别": record["category"],
            "金额（元）": record["amount"],
            "备注": record["note"],
        }
        for record in records
    ]
    st.dataframe(
        rows,
        hide_index=True,
        column_config={"金额（元）": st.column_config.NumberColumn(format="%.2f")},
    )


def page_add(records):
    ui.heading("A LITTLE MOMENT", "新增记账", "记下一笔刚刚发生的收入或支出。")
    record_type = st.radio(
        "类型", list(_TYPE_LABELS), format_func=_TYPE_LABELS.__getitem__, horizontal=True,
    )
    form_version = st.session_state.get("add_form_version", 0)
    with st.form(f"add-{form_version}"):
        fields = _record_fields(record_type, {"date": date.today().isoformat()})
        submitted = st.form_submit_button("保存记录", type="primary")
    if not submitted:
        return

    fields["record_type"] = fields.pop("type")
    try:
        record = add_record(**fields)
    except ValueError as exc:
        st.error(f"保存失败：{exc}")
        return
    st.session_state["add_form_version"] = form_version + 1
    st.session_state["notice"] = f"已保存：{_TYPE_LABELS[record_type]} {record['amount']:.2f} 元"
    st.rerun()


def page_recent(records):
    ui.heading("LITTLE MOMENTS", "最近记录", "按记账日期查看最近 10 笔收支。")
    if records:
        _record_table(get_recent_records(records))
    else:
        ui.empty_state("还没有流水", "新增第一笔记录后，这里会显示最新的收支。")
        st.button("＋ 记一笔", type="primary", on_click=_navigate, args=("新增记账",))


def page_filter(records):
    ui.heading("FIND A RECORD", "筛选统计", "组合筛选条件，看看这段时间的每笔收支。")
    today = date.today()
    record_dates = [date.fromisoformat(record["date"]) for record in records]
    date_bounds = {
        "min_value": min([date(1900, 1, 1), *record_dates]),
        "max_value": max([date(2100, 12, 31), today, *record_dates]),
    }
    with st.container(border=True):
        ui.heading("FILTERS", "筛选条件", "留空的条件不限。", panel=True)
        kinds, dates, amounts = st.columns(3)
        record_type = kinds.selectbox(
            "类型", [None, *_TYPE_LABELS],
            format_func=lambda value: _TYPE_LABELS.get(value, "全部"),
        )
        categories = _CATEGORIES.get(record_type, list(dict.fromkeys(EXPENSE_CATEGORIES + INCOME_CATEGORIES)))
        category = kinds.selectbox("类别", ["全部", *categories])
        if category not in categories:
            category = None
        start = dates.date_input("开始日期", value=None, **date_bounds)
        end = dates.date_input("结束日期", value=None, **date_bounds)
        minimum = amounts.number_input("最小金额", min_value=0.0, value=None, step=0.01, format="%.2f")
        maximum = amounts.number_input("最大金额", min_value=0.0, value=None, step=0.01, format="%.2f")
    try:
        selected = filter_records(
            records, start_date=start.isoformat() if start else None,
            end_date=end.isoformat() if end else None,
            category=category, record_type=record_type, min_amount=minimum, max_amount=maximum,
        )
        summary = calculate_summary(selected)
    except ValueError as exc:
        st.error(str(exc))
        return

    income, expense, balance, count = st.columns(4)
    income.metric("总收入", f"¥{summary['income']:,.2f}")
    expense.metric("总支出", f"¥{summary['expense']:,.2f}")
    balance.metric("结余", f"¥{summary['balance']:,.2f}")
    count.metric("笔数", summary["count"])
    if selected:
        _record_table(selected)
    elif not records:
        ui.empty_state("还没有流水", "记下第一笔收入或支出，再来看看你的收支统计。")
        st.button("＋ 记一笔", type="primary", on_click=_navigate, args=("新增记账",))
    else:
        ui.empty_state("没有符合条件的记录", "可以调整日期、类别或金额范围。")


def page_charts(records):
    ui.heading("THE BIG PICTURE", "数据图表", "查看全部记录的收支对比与支出类别分布。")
    if not records:
        ui.empty_state("图表在等第一笔记录", "新增收入或支出后，图表会自动生成。")
        return
    try:
        render_charts(records)
    except ValueError as exc:
        st.error(f"图表统计失败：{exc}")


def page_manage(records):
    ui.heading("TIDY THE BOOK", "编辑与删除", "选中一笔流水后修改，删除前需要确认。")
    if not records:
        ui.empty_state("暂无可编辑的记录", "记下第一笔流水后，就可以在这里管理。")
        return

    by_id = {record["id"]: record for record in get_recent_records(records, limit=len(records))}

    def label(record_id):
        record = by_id[record_id]
        return (
            f"{record['date']} · {_TYPE_LABELS[record['type']]} · {record['category']} · "
            f"¥{record['amount']:,.2f} · {record_id}"
        )

    record_id = st.selectbox("选择记录", list(by_id), format_func=label)
    record = by_id[record_id]
    record_type = st.radio(
        "修改类型", list(_TYPE_LABELS), index=list(_TYPE_LABELS).index(record["type"]),
        format_func=_TYPE_LABELS.__getitem__, horizontal=True, key=f"edit-type-{record_id}",
    )
    with st.form(f"edit-{record_id}"):
        fields = _record_fields(record_type, record)
        submitted = st.form_submit_button("保存修改", type="primary")

    if submitted:
        try:
            updated = update_record(record_id, fields)
        except ValueError as exc:
            st.error(f"修改失败：{exc}")
            return
        if updated:
            st.session_state["notice"] = "已保存修改。"
            st.rerun()
        st.warning("这条记录已被删除，请刷新后重试。")

    with st.expander("删除这条记录"):
        confirmed = st.checkbox("确认永久删除", key=f"confirm-delete-{record_id}")
        if st.button("删除记录", disabled=not confirmed) and confirmed:
            try:
                deleted = delete_record(record_id)
            except ValueError as exc:
                st.error(f"删除失败：{exc}")
                return
            if deleted:
                st.session_state["notice"] = "已删除记录。"
                st.rerun()
            st.warning("这条记录已被删除，请刷新后重试。")


def page_export(records):
    ui.heading("TAKE IT WITH YOU", "导出 CSV", f"将当前的 {len(records):,} 笔收支下载为 CSV。")
    st.download_button(
        "下载 CSV", data=export_csv(records), file_name="records.csv", mime="text/csv",
    )


def main():
    st.set_page_config(page_title="拾光账本 · Pocket Days", page_icon=str(ui.BRAND_ICON), layout="wide")
    ui.theme()
    try:
        records = load_records()
    except ValueError as exc:
        st.error(f"账本读取失败：{exc}")
        return

    pages = {
        "新增记账": page_add,
        "最近记录": page_recent,
        "筛选统计": page_filter,
        "数据图表": page_charts,
        "编辑与删除": page_manage,
        "导出 CSV": page_export,
    }
    with st.sidebar:
        ui.brand()
        page = st.radio("工作台", list(_NAV_LABELS), format_func=_NAV_LABELS.__getitem__, key="ledger_page")
        ui.sidebar_note(len(records))
    today = date.today()
    ui.topbar(page, today)
    if message := st.session_state.pop("notice", None):
        st.success(message)
    if page == "收支总览":
        ui.overview(records, today, _navigate)
    else:
        pages[page](records)


if __name__ == "__main__":
    main()
