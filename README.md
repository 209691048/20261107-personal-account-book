# 拾光账本 · Pocket Days

个人记账本 —— 福州大学软件工程现场编程作业。
基于 **Python + Streamlit + JSON** 的轻量级 Web 记账应用，界面设计参考「拾光账本」风格，主打极简、好用、本地存储。

## 技术栈

- **前端框架**：Streamlit 1.67
- **数据处理**：pandas 3.0
- **数据存储**：本地 JSON 文件（`data/records.json`）
- **界面设计**：深绿 + 浅绿配色，圆角卡片，数据图表可视化

## 目录结构

```
personal-account-book/
├── app.py            # 主界面与模块集成
├── models.py         # 数据模型（uuid id / income-expense 类型）
├── storage.py        # JSON 读写与持久化
├── add_record.py     # 新增记账表单
├── view_records.py   # 收支明细查看
├── filter_records.py # 条件筛选
├── statistics.py     # 收支统计与汇总
├── charts.py         # 柱状图 / 环形图可视化
├── manage_records.py # 编辑与删除记录
├── export_data.py    # CSV 导出
├── assets/           # UI 资源（设计稿、图标、样式）
├── data/             # 本地数据文件
├── docs/             # 项目文档
├── tests/            # 单元测试
└── screenshots/      # 演示截图
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8501 即可使用。

## 核心功能

- 📝 **记一笔**：快速记录收入 / 支出，支持分类、日期、备注
- 📊 **总览仪表盘**：本月结余、收入、支出一目了然，附收支趋势柱状图
- 🔍 **筛选统计**：按时间、类型、分类多维度筛选
- 💳 **收支明细**：完整交易列表查看
- 📈 **数据图表**：收支构成环形图、月度趋势对比
- 📤 **导出 CSV**：数据导出备份

## 协作说明

10 人小组协作开发，按模块分工提交，`app.py` 为主入口集成各业务模块。
数据格式严格遵循开发规范：`id` 用 uuid4，`type` 仅 `income` / `expense`，金额为正数，`created_at` 用 ISO 8601 带时区。
