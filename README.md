# 拾光账本 · Pocket Days

个人记账本 —— 福州大学软件工程现场编程作业。
基于 **Python + Streamlit + JSON** 的轻量级 Web 记账应用，界面设计参考「拾光账本」风格，主打极简、好用、本地存储。

[下载 v1.0.0](https://github.com/platforzation/20261107-personal-account-book/releases/tag/v1.0.0) · [演示视频](https://github.com/platforzation/20261107-personal-account-book/blob/main/screenshots/PocketDays-v1.0.0-demo.mkv)

## 技术栈与运行环境

- **源码运行环境**：Python 3.10+；本机验证为 Windows x64、Python 3.12.14
- **前端框架**：Streamlit `>=1.35,<2`；本机验证版本为 1.67.0
- **数据处理**：pandas `>=2.0,<3`、Altair；本机验证版本分别为 2.3.3、6.3.0
- **数据存储**：本地 JSON；源码版与 Windows 免安装版的数据目录不同，见下文
- **界面设计**：深绿 + 浅绿配色，圆角卡片，数据图表可视化

## 目录结构

```
personal-account-book/
├── app.py            # 主界面与模块集成
├── models.py         # 数据模型（uuid id / income-expense 类型）
├── storage.py        # JSON 读写与持久化
├── add_record.py     # 创建记录并保存
├── view_records.py   # 收支明细查看
├── filter_records.py # 条件筛选
├── account_statistics.py # 收支统计与汇总
├── statistics.py     # 原统计接口的兼容入口
├── charts.py         # 收支对比与支出类别图表
├── manage_records.py # 编辑与删除记录
├── export_data.py    # CSV 导出
├── assets/           # 独立界面设计稿
├── ui/               # 运行界面的图片和样式
├── data/             # 本地数据文件
├── docs/             # 项目文档
├── tests/            # 单元测试
└── screenshots/      # 演示资料（含 MKV 视频）
```

## 快速开始

### 方式一：Windows 免安装版

在 [v1.0.0 Release](https://github.com/platforzation/20261107-personal-account-book/releases/tag/v1.0.0) 下载 **PocketDays-v1.0.0-windows-x64.zip**。

1. 完整解压 ZIP，双击 `PocketDays.exe`，无需另行安装 Python。
2. 保留同目录的 `_internal` 文件夹，不能只复制 EXE，也不要在压缩包内直接运行。
3. 程序自动打开默认浏览器；未自动打开时，访问 [http://127.0.0.1:18501](http://127.0.0.1:18501)。
4. 使用期间保留启动窗口；退出时按 `Ctrl+C` 或关闭启动窗口。仅关闭浏览器标签页不会停止服务。

发布包面向 Windows 10/11 x64，已在当前 Windows 电脑上验证，尚未在另一台全新电脑上验证。目前未发布 macOS、Linux 或 32 位 Windows 可执行包；本次也未完成 macOS / Linux 实机验证。

### 方式二：从源码运行

安装 Python 3.10+，下载并解压 v1.0.0 源码，或克隆本仓库。在项目根目录打开 PowerShell：

```powershell
# 创建虚拟环境
python -m venv .venv

# 安装依赖
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 启动源码版
.\.venv\Scripts\python.exe -m streamlit run app.py
```

启动后访问 [http://127.0.0.1:8501](http://127.0.0.1:8501)。上面的命令直接调用虚拟环境，无需激活脚本或修改 PowerShell 执行策略。

下载软件和首次安装依赖需要联网；核心记账功能及运行界面的图片、样式使用本地资源，日常记账可离线完成。

## 数据目录与备份

| 运行方式 | 默认地址 | 账本位置 |
|---|---|---|
| 源码版 | `http://127.0.0.1:8501` | 项目目录下的 `data/records.json` |
| Windows 免安装版 | `http://127.0.0.1:18501` | `%LOCALAPPDATA%\PocketDays\records.json` |

- 账本文件在首次成功保存记录时创建；没有文件时显示空账本。
- 仓库只跟踪 `data/records.example.json`，真实的 `data/records.json` 已被 Git 忽略。
- 更新前请停止应用，将现有账本备份到程序目录之外。
- 在资源管理器地址栏输入 `%LOCALAPPDATA%\PocketDays` 可打开免安装版的数据目录。
- 从源码版迁移到免安装版时，先关闭应用并备份两个位置的现有账本，再复制 `records.json`；不要直接覆盖已有数据。
- 服务默认只监听 `127.0.0.1`。源码版仅支持单个服务进程操作同一账本；进程内的 `RLock` 不等于跨进程锁。Windows 启动器另提供同一用户下的单实例保护。
- 损坏 JSON 会明确报错并阻止覆盖；临时文件和原子替换减少写入中断造成的损坏，但不能代替备份。

## 核心功能

- 🏡 **收支总览**：月度收支卡片、近半年或近七天趋势、本月支出占比和最近流水

- 📝 **记一笔**：快速记录收入 / 支出，支持分类、日期、备注
- 🔍 **筛选统计**：按日期、类型、类别和金额筛选，查看收入、支出、结余及笔数
- 💳 **收支明细**：查看最近 10 笔，或在筛选页查看全部符合条件的记录
- 📈 **数据图表**：收支对比、支出类别分布及分类明细表
- ✏️ **编辑与删除**：选择记录后修改，删除需要确认
- 📤 **导出 CSV**：下载全部记录。可能被电子表格识别为公式的文本会加单引号前缀，原始 JSON 保留原值

`assets/shiguang.html` 是独立的界面设计稿，使用示例数据。运行界面使用 `ui/` 中的品牌图片和样式，并从本地账本读取实际数据。

## 运行测试

在项目根目录使用同一个虚拟环境执行。`pytest` 是额外的测试依赖：

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

v1.0.0（源码提交 `2d1981a`）在本机 Python 3.12.14 / Streamlit 1.67.0 / pandas 2.3.3 环境复测：**72 项测试及 80 个子测试通过**。Windows 发布包另完成实际 EXE 的新增、筛选、图表、编辑删除、CSV 下载、单实例和重启持久化检查。

[PR #15](https://github.com/platforzation/20261107-personal-account-book/pull/15) 与 [PR #17](https://github.com/platforzation/20261107-personal-account-book/pull/17) 还记录了 Python 3.10 / Streamlit 1.35、Python 3.13 / Streamlit 1.67 两组测试结果；这不代表所有操作系统和依赖组合均已验证。

## 演示视频

[下载或查看视频文件：PocketDays-v1.0.0-demo.mkv](https://github.com/platforzation/20261107-personal-account-book/blob/main/screenshots/PocketDays-v1.0.0-demo.mkv)

GitHub 可能无法直接预览 MKV，请在文件页面下载后使用本地视频播放器观看。

## 协作说明

10 人小组协作开发，按模块分工提交，`app.py` 为主入口集成各业务模块。
数据格式严格遵循开发规范：`id` 用 uuid4，`type` 仅 `income` / `expense`，金额为正数，`created_at` 用 ISO 8601 带时区。

