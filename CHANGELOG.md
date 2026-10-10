# Changelog

本文件记录 funhtml 的版本变更，按版本倒序排列，分类为 新增 / 修复 / 变更 / 废弃。

## [1.0.4] - 未发布

### 新增

- README 补充项目简介、安装命令与最小可运行示例，并附上「关于 farfarfun」区块
- 新增 CHANGELOG.md
- `pyproject.toml` 显式声明 `license = "MIT"`
- 补充 `DataFrame2Html` 类文档，公开方法补全类型标注
- 新增 `src/funhtml/py.typed`（PEP 561 类型标注标记），下游可直接使用本包的类型信息
- `tests/` 新增 smoke 测试套件（此前仓库没有 `tests/` 目录）
- `tests/` 补充图片列、空 DataFrame、自定义 `pass_words`、callable/generator 内容、属性渲染等边界测试
- 新增 `pandas` 可选依赖 extra（`pip install 'funhtml[pandas]'`），README 的 DataFrame 示例同步补充安装说明
- `pyproject.toml` 补充 `ruff` 开发依赖与 `[tool.ruff]` lint/format 配置，提供可审计的执行路径
- `.gitignore` 补充 `*.rar` 规则
- `tests/` 补充 `Safe`、`Var`、`Block` 占位替换、`copy()`、`register_all` 动态注册、callable 属性值等公开能力的测试
- 新增 `.github/FUNDING.yml`（GitHub Sponsors 链接）

### 修复

- 修复 `funhtml/__init__.py` 中 `__all__` 声明了 `DataFrame2Html` 但未实际导入的问题，现可通过 `from funhtml import DataFrame2Html` 正常使用
- 修复 `pd2html.py` 中 `dataframe_to_html` docstring 示例引用了不存在的 `df_to_html` 函数名的问题
- 修复 `ruff check` 新增配置后暴露的历史遗留问题（`RUF012` 可变类属性默认值改用 `ClassVar`、`SIM103` 简化布尔返回）

### 变更

- **破坏性变更**：`requires-python` 下限由 `>=3.8` 提升到 `>=3.10`（3.8/3.9 已 EOL）。迁移方法：升级到 Python 3.10 及以上；仍需在 3.8/3.9 上安装的项目请固定 `funhtml==1.0.3`
- `pyproject.toml` 的 `description` 由占位的 `funhtml` 改为真实项目简介
- `pd2html.py` 中的类型标注由 `typing.Optional/Dict/List` 改为 Python 3.10 内置泛型写法（`X | None`、`dict[...]`、`list[...]`）
- `pyhtml.py` 的模块说明、docstring 与注释翻译为中文（保留代码示例中的 HTML/API 字面量）
- `pyhtml.py` 为 `Tag.__call__`、`Tag.name`、`Tag.copy`、`Tag.__setitem__`、`Block.render` 以及各标签基类补充中文 docstring
- `pd2html.py` 为 `DataFrame2Html` 的 `get_title`、`get_td`、`get_tr`、`html`、`html_str` 补充参数与返回值说明
- `.gitignore` 补充 `*.pyc`、`*.db`、`.idea/`、`.vscode/`、`.run/`、`logs/`、`node_modules/` 规则
- `.gitignore` 忽略 `uv.lock`，仓库不再跟踪锁文件

## [1.0.3] - 2026-01-16

### 新增

- 新增 `pd2html` 模块：`DataFrame2Html` 类与 `dataframe_to_html` 函数，可把 pandas DataFrame 转成 HTML 表格，自动识别图片列与 `:url` 配对的链接列
- `funhtml` 顶层导出 `dataframe_to_html`

## [1.0.2] - 2026-01-16

### 变更

- 仅版本号升级，无功能变更

## [1.0.1] - 2026-01-16（仅 git tag，未发布到 PyPI）

### 新增

- 首个版本：`pyhtml` 纯 Python HTML 生成 DSL，支持标签拼装与属性渲染、`Block` 占位块替换、`Safe` 免转义内容、`Var` 上下文取值，以及自闭合标签与空白敏感标签
