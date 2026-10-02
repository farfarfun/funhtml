# Changelog

本文件记录 funhtml 的版本变更，按版本倒序排列，分类为 新增 / 修复 / 变更 / 废弃。

## [未发布]

### 新增

- README 补充项目简介、安装命令与最小可运行示例，并附上「关于 farfarfun」区块
- 新增 CHANGELOG.md
- `pyproject.toml` 显式声明 `license = "MIT"`
- 补充 `DataFrame2Html` 类文档，公开方法补全类型标注
- `tests/` 补充图片列、空 DataFrame、自定义 `pass_words`、callable/generator 内容、属性渲染等边界测试
- 新增 `pandas` 可选依赖 extra（`pip install 'funhtml[pandas]'`），README 的 DataFrame 示例同步补充安装说明
- `pyproject.toml` 补充 `ruff` 开发依赖与 `[tool.ruff]` lint/format 配置，提供可审计的执行路径
- `.gitignore` 补充 `*.rar` 规则
- `tests/` 补充 `Safe`、`Var`、`Block` 占位替换、`copy()`、`register_all` 动态注册、callable 属性值等公开能力的测试

### 修复

- 修复 `funhtml/__init__.py` 中 `__all__` 声明了 `DataFrame2Html` 但未实际导入的问题，现可通过 `from funhtml import DataFrame2Html` 正常使用
- 修复 `pd2html.py` 中 `dataframe_to_html` docstring 示例引用了不存在的 `df_to_html` 函数名的问题
- 修复 `ruff check` 新增配置后暴露的历史遗留问题（`RUF012` 可变类属性默认值改用 `ClassVar`、`SIM103` 简化布尔返回）

### 变更

- `pd2html.py` 中的类型标注由 `typing.Optional/Dict/List` 改为 Python 3.10 内置泛型写法（`X | None`、`dict[...]`、`list[...]`）
- `pyhtml.py` 的模块说明、docstring 与注释翻译为中文（保留代码示例中的 HTML/API 字面量）
- `.gitignore` 补充 `*.pyc`、`*.db`、`.idea/`、`.vscode/`、`.run/`、`logs/`、`node_modules/` 规则

## [1.0.4] 及之前

早期版本变更未系统记录。
