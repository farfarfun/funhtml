# funhtml

轻量级纯 Python HTML 生成库，核心 `pyhtml` DSL 无第三方运行时依赖。提供两套能力：一是用 Python 对象拼装 HTML 标签的 `pyhtml` DSL（类似 PyHTML），二是把 pandas DataFrame 一键转换成 HTML 表格的 `dataframe_to_html` 便捷函数（自动识别图片列、URL 链接列，需要可选依赖 pandas）。

## 安装

```bash
pip install funhtml
```

## 快速上手

### 1. 用 pyhtml 拼装 HTML 标签

```python
from funhtml.pyhtml import div, p, html, body

page = html(body(div(p("hello funhtml"))))
print(page.render())
# <!DOCTYPE html>
# <html>
#   <body>
#     <div>
#       <p>
#         hello funhtml
#       </p>
#     </div>
#   </body>
# </html>
```

### 2. 把 DataFrame 转成 HTML 表格

该功能依赖 pandas，未随核心包默认安装，需要装带 `pandas` extra 的版本：

```bash
pip install 'funhtml[pandas]'
```

```python
import pandas as pd
from funhtml import dataframe_to_html

df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
html_str = dataframe_to_html(df)
print(html_str)
```

`dataframe_to_html` 默认会跳过名为 `url` 的列，并将列名以 `:url` 结尾的列当作链接目标；列名包含 `img`/`image`/`pic` 等关键词时会自动渲染为 `<img>` 标签。

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。
