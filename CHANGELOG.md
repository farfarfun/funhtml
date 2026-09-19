# Changelog

本文件记录 funhtml 的版本变更，按版本倒序排列，分类为 新增 / 修复 / 变更 / 废弃。

## [未发布]

### 新增

- README 补充项目简介、安装命令与最小可运行示例，并附上「关于 farfarfun」区块
- 新增 CHANGELOG.md
- `pyproject.toml` 显式声明 `license = "MIT"`
- 补充 `DataFrame2Html` 类文档，公开方法补全类型标注
- `tests/` 补充图片列、空 DataFrame、自定义 `pass_words`、callable/generator 内容、属性渲染等边界测试

### 修复

- 修复 `funhtml/__init__.py` 中 `__all__` 声明了 `DataFrame2Html` 但未实际导入的问题，现可通过 `from funhtml import DataFrame2Html` 正常使用

### 变更

- `pd2html.py` 中的类型标注由 `typing.Optional/Dict/List` 改为 Python 3.10 内置泛型写法（`X | None`、`dict[...]`、`list[...]`）
- `pyhtml.py` 的模块说明、docstring 与注释翻译为中文（保留代码示例中的 HTML/API 字面量）
- `.gitignore` 补充 `*.pyc`、`*.db`、`.idea/`、`.vscode/`、`.run/`、`logs/`、`node_modules/` 规则

## [1.0.4] 及之前

早期版本变更未系统记录。
