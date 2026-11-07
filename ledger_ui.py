"""View helpers for the Pocket Days layout."""

from base64 import b64encode
from datetime import date, timedelta
from functools import cache
from html import escape
from pathlib import Path

import streamlit as st

from account_statistics import calculate_summary, category_totals
from view_records import get_recent_records


_UI_DIR = Path(__file__).resolve().parent / "ui"
BRAND_ICON = _UI_DIR / "brand.png"
_COLORS = ("#348873", "#8cbda9", "#a6afe6", "#edb685", "#efca9b", "#709688", "#c59fc7", "#afbd90")


@cache
def _art(filename):
    encoded = b64encode((_UI_DIR / filename).read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def theme():
    _html(f"<style>{(_UI_DIR / 'theme.css').read_text(encoding='utf-8')}</style>")


def brand():
    _html(f'<div class="sg-brand"><img src="{_art("brand.png")}" alt="">'
          '<div><strong>拾光账本</strong><small>POCKET DAYS</small></div></div>')


def sidebar_note(record_count):
    _html(f'<div class="sg-sidebar-note"><img src="{_art("wallet.png")}" alt="">'
          '<strong>给生活一点「账」力</strong><p>记录每一笔，安排好每一天。</p></div>'
          f'<div class="sg-status">本地存储 <span>{record_count:,} 笔记录</span></div>')


def topbar(page, today):
    _html(
        f'<header class="sg-topbar"><div>我的空间 <span>/</span> <strong>{escape(page)}</strong></div>'
        f'<div class="sg-topdate"><time datetime="{today.isoformat()}">{today:%Y 年 %m 月}</time>'
        '<span class="sg-avatar" aria-hidden="true">拾</span></div></header>'
    )


def heading(kicker, title, description, *, panel=False):
    kind = "sg-panel-heading" if panel else "sg-page-heading"
    _html(f'<div class="sg-heading {kind}"><small>{escape(kicker)}</small>'
          f'<h2>{escape(title)}</h2><p>{escape(description)}</p></div>')


def empty_state(title, description):
    _html(
        f'<div class="sg-empty"><img src="{_art("empty-state.png")}" alt="">'
        f'<strong>{escape(title)}</strong><p>{escape(description)}</p></div>'
    )


def _periods(today, weekly):
    if weekly:
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        return [(day.isoformat(), f"{day.month}/{day.day}") for day in days]
    month = today.year * 12 + today.month - 1
    months = [divmod(month - i, 12) for i in range(5, -1, -1)]
    return [(f"{year:04d}-{index + 1:02d}", f"{index + 1} 月") for year, index in months]


def _money(amount):
    return f"−¥{abs(amount):,.2f}" if amount < 0 else f"¥{amount:,.2f}"


def _summary_cards(summary, records):
    income_count = sum(record["type"] == "income" for record in records)
    cards = (
        ("balance", "本月结余", "↗", summary["balance"], f"本月共 {summary['count']} 笔记录"),
        ("income", "本月收入", "↙", summary["income"], f"共 {income_count} 笔收入"),
        ("expense", "本月支出", "↗", summary["expense"], f"共 {len(records) - income_count} 笔支出"),
    )
    content = [
        f'<section class="sg-card sg-{kind}"><div class="sg-card-label">{label}'
        f'<span aria-hidden="true">{icon}</span></div><div class="sg-card-money">{_money(amount)}</div>'
        f'<div class="sg-card-foot">{detail}</div></section>'
        for kind, label, icon, amount, detail in cards
    ]
    _html('<div class="sg-summary" aria-label="本月收支">' + "".join(content) + "</div>")


def _trend(records, today, weekly):
    periods = _periods(today, weekly)
    size = 10 if weekly else 7
    groups = {key: [] for key, _ in periods}
    for record in records:
        key = record["date"][:size]
        if key in groups:
            groups[key].append(record)
    totals = [calculate_summary(groups[key]) for key, _ in periods]
    peak = max((max(row["income"], row["expense"]) for row in totals), default=0)
    legend = '<div class="sg-legend"><span>收入</span><span>支出</span></div>'
    bars = []
    descriptions = []
    for (_, label), total in zip(periods, totals):
        income = total["income"] / peak * 100 if peak else 0
        expense = total["expense"] / peak * 100 if peak else 0
        detail = f"{label} 收入 {_money(total['income'])}，支出 {_money(total['expense'])}"
        descriptions.append(detail)
        bars.append(
            f'<div class="sg-bar-group" title="{detail}"><div class="sg-bar-pair">'
            f'<i style="height:{income:.3f}%"></i><i style="height:{expense:.3f}%"></i></div>'
            f'<small>{label}</small></div>'
        )
    notice = "" if peak else '<p class="sg-chart-empty">这段时间还没有收支</p>'
    _html(legend + f'<div class="sg-trend" role="img" aria-label="{"；".join(descriptions)}">'
          + "".join(bars) + notice + "</div>")


def _mix(records, total):
    categories = sorted(category_totals(records).items(), key=lambda item: (-item[1], item[0]))
    if not categories:
        empty_state("本月暂无支出", "记下一笔支出，分类占比就会显示在这里。")
        return
    stops = []
    labels = []
    start = 0.0
    for index, (category, amount) in enumerate(categories):
        share = amount / total * 100
        end = 100 if index == len(categories) - 1 else start + share
        color = _COLORS[index % len(_COLORS)]
        stops.append(f"{color} {start:.4f}% {end:.4f}%")
        labels.append(
            f'<li><i style="background:{color}"></i><span>{escape(category)}</span>'
            f'<strong>{share:.0f}%</strong></li>'
        )
        start = end
    _html(f'<div class="sg-mix"><div class="sg-ring" style="--mix:conic-gradient({",".join(stops)})">'
          f'<div><small>本月支出</small><strong>{_money(total)}</strong></div></div>'
          f'<ul>{"".join(labels)}</ul></div>')


def _recent(records):
    if not records:
        empty_state("还没有流水", "点击「记一笔」，从第一笔收入或支出开始。")
        return
    rows = []
    for record in get_recent_records(records, limit=4):
        income = record["type"] == "income"
        label = escape(record["note"].strip() or record["category"])
        date_text = date.fromisoformat(record["date"]).strftime("%m/%d")
        rows.append(
            '<li><span class="sg-entry-icon" aria-hidden="true">' + ("↙" if income else "↗") + "</span>"
            f'<div><strong>{label}</strong><small>{escape(record["category"])} · {date_text}</small></div>'
            f'<b class="sg-{"in" if income else "out"}">{"+" if income else "−"}{_money(record["amount"])}</b></li>'
        )
    _html('<ul class="sg-entries">' + "".join(rows) + "</ul>")


def overview(records, today, navigate):
    intro, action = st.columns([4, 1])
    with intro:
        _html('<div class="sg-hero"><div>✳ &nbsp; YOUR FINANCIAL CORNER <span>轻松记账</span></div>'
              '<h1>把日子过好，<em>也把账记好。</em></h1>'
              '<p>每一笔小小的记录，都在帮你靠近理想生活。</p></div>')
    with action:
        st.button("＋ 记一笔", type="primary", on_click=navigate, args=("新增记账",))

    month = [record for record in records if record["date"][:7] == today.isoformat()[:7]]
    try:
        summary = calculate_summary(month)
    except ValueError as exc:
        st.error(str(exc))
        return
    _summary_cards(summary, month)

    trend, mix = st.columns([3, 2])
    with trend, st.container(border=True):
        heading("CASH FLOW", "收支小趋势", "对照这段时间的收入和支出", panel=True)
        period = st.radio("趋势范围", ["近 6 个月", "近 7 天"], horizontal=True, label_visibility="collapsed")
        try:
            _trend(records, today, weekly=period == "近 7 天")
        except ValueError as exc:
            st.error(str(exc))
    with mix, st.container(border=True):
        heading("SPENDING MIX", "钱花在哪儿了", "本月支出类别分布", panel=True)
        _mix(month, summary["expense"])

    recent, note = st.columns([3, 2])
    with recent, st.container(border=True):
        heading("LITTLE MOMENTS", "最近的收支记录", "每一笔，都是生活的小片段", panel=True)
        _recent(records)
        if records:
            st.button("查看全部流水 ↗", on_click=navigate, args=("筛选统计",))
    with note:
        _html('<aside class="sg-note"><small>THIS WEEK’S NOTE <span>✳</span></small>'
              '<blockquote>认真生活的人，<br>连零钱都有光。</blockquote>'
              '<p>把今天妥善收藏。</p></aside>')
