# 拾光账本 · Pocket Days

个人记账本 —— 福州大学软件工程现场编程作业。
基于 **Python + Streamlit + JSON** 的轻量级 Web 记账应用，界面设计参考「拾光账本」风格，主打极简、好用、本地存储。

## 技术栈

- **运行环境**：Python 3.10+
- **前端框架**：Streamlit 1.x
- **数据处理**：pandas 2.x、Altair
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
├── account_statistics.py # 收支统计与汇总
├── statistics.py     # 原统计接口的兼容入口
├── charts.py         # 收支对比与支出类别图表
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

在项目根目录运行后，打开 http://127.0.0.1:8501。默认仅允许本机访问。账本供单个 Streamlit 服务进程使用。

`data/records.json` 由应用首次保存时创建，Git 只跟踪 `data/records.example.json`。从旧版更新时，如果已有记账数据，请先将 `data/records.json` 备份到仓库外，更新后再放回原路径。

## 核心功能

- 📝 **记一笔**：快速记录收入 / 支出，支持分类、日期、备注
- 🔍 **筛选统计**：按日期、类型、类别和金额筛选，查看收入、支出、结余及笔数
- 💳 **收支明细**：查看最近 10 笔，或在筛选页查看全部符合条件的记录
- 📈 **数据图表**：收支对比、支出类别分布及分类明细表
- ✏️ **编辑与删除**：选择记录后修改，删除需要确认
- 📤 **导出 CSV**：下载全部记录。可能被电子表格识别为公式的文本会加单引号前缀，原始 JSON 保留原值

`assets/shiguang.html` 是独立的界面设计稿，使用示例数据。可从该文件直接预览。

## 运行测试

```bash
python -m pip install pytest
python -m pytest -q
```

## 协作说明

10 人小组协作开发，按模块分工提交，`app.py` 为主入口集成各业务模块。
数据格式严格遵循开发规范：`id` 用 uuid4，`type` 仅 `income` / `expense`，金额为正数，`created_at` 用 ISO 8601 带时区。
