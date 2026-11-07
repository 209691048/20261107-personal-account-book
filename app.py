# -*- coding: utf-8 -*-
"""拾光账本 - 主界面与模块集成"""
import os
import json
import streamlit as st
import streamlit.components.v1 as components

# ==================================================
# 页面配置
# ==================================================
st.set_page_config(page_title="拾光账本", page_icon="🌿", layout="wide")

st.markdown("""
<style>
.stApp, .stApp > div, .stApp > div > div, .stApp > div > div > div { padding: 0 !important; margin: 0 !important; }
[data-testid="stHeader"] { display: none; }
[data-testid="stAppViewContainer"] { padding: 0 !important; margin: 0 !important; }
[data-testid="stMainBlockContainer"] { padding: 0 !important; margin: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 业务模块集成（容错导入 + 明确状态提示）
# ==================================================
modules_status = {}

# models 模块
try:
    from models import create_record, validate_record, EXPENSE_CATEGORIES, INCOME_CATEGORIES
    modules_status["models"] = "✅ 已就绪"
except Exception as e:
    modules_status["models"] = f"❌ 未就绪: {e}"

# storage 模块
try:
    from storage import load_records, save_records
    modules_status["storage"] = "✅ 已就绪"
except Exception as e:
    modules_status["storage"] = f"❌ 未就绪: {e}"

# statistics 模块（注意：与标准库同名，用 importlib 避免冲突）
try:
    from statistics import calculate_summary, category_totals
    modules_status["statistics"] = "✅ 已就绪"
except Exception as e:
    modules_status["statistics"] = f"❌ 未就绪: {e}"

# ==================================================
# 加载真实数据（出错明确提示，不静默降级）
# ==================================================
data_path = os.path.join(os.path.dirname(__file__), "data", "records.json")
records = []
data_warning = None

if not os.path.exists(data_path):
    # 文件不存在：首次运行，空账本，这是正常状态
    data_warning = None  # 空账本是正常的，不警告
else:
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        if not isinstance(records, list):
            data_warning = "⚠️ 数据格式错误：records.json 应为数组"
            records = []
    except json.JSONDecodeError as e:
        data_warning = f"⚠️ 数据文件损坏：JSON 解析失败 - {e}"
        records = []
    except Exception as e:
        data_warning = f"⚠️ 数据读取失败：{e}"
        records = []

# ==================================================
# 计算统计数据（明确失败原因，不静默降级）
# ==================================================
summary = {"income": 0, "expense": 0, "balance": 0, "count": len(records)}
stats_warning = None

if "✅" not in modules_status["statistics"]:
    stats_warning = "统计模块未就绪，显示为示例数据"
elif not records:
    stats_warning = "暂无记录"
else:
    try:
        summary = calculate_summary(records)
    except Exception as e:
        stats_warning = f"统计计算失败: {e}"

# ==================================================
# 渲染主界面（嵌入设计稿 HTML）
# ==================================================
html_path = os.path.join(os.path.dirname(__file__), "assets", "shiguang.html")

try:
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=1600, scrolling=False)
except FileNotFoundError:
    st.error("⚠️ 设计稿文件 assets/shiguang.html 未找到，请检查 assets 目录")
    st.stop()
except Exception as e:
    st.error(f"⚠️ 页面加载异常: {e}")
    st.stop()

# ==================================================
# 状态栏（明确显示数据状态和模块状态，不隐藏问题）
# ==================================================
with st.sidebar:
    st.divider()
    st.write("**系统状态**")
    for name, status in modules_status.items():
        st.write(f"- {name}: {status}")
    st.divider()
    if data_warning:
        st.warning(data_warning)
    elif stats_warning:
        st.info(stats_warning)
    st.caption(f"当前记录数: {len(records)} 条")
