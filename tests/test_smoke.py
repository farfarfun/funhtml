"""轻量冒烟测试（smoke tests）for funhtml.

范围说明：本测试套件只做“最基本可用性”验证——能否正常导入、核心公开
API 能否以简单参数构造/调用并产生预期的字符串输出。不追求覆盖所有
边界情况，也不测试内部私有实现细节。

funhtml 是一个纯 Python 的 HTML 生成库（无第三方运行时依赖），因此
这里不需要 mock 任何网络 / 数据库 / 云服务调用。
"""

import subprocess
import sys


def test_import_top_level_package():
    """顶层包应当可以正常导入。"""
    import funhtml

    assert funhtml is not None


def test_import_submodules():
    """已知的两个公开子模块应当可以正常导入。"""
    import funhtml.pd2html
    import funhtml.pyhtml

    assert funhtml.pd2html is not None
    assert funhtml.pyhtml is not None


def test_dataframe_to_html_reexported_at_top_level():
    """funhtml.__init__ 中显式导入并 re-export 的函数应当可用。"""
    from funhtml import dataframe_to_html

    assert callable(dataframe_to_html)


def test_dataframe2html_not_actually_exported_from_top_level():
    """已知问题（不在本次冒烟测试范围内修复）：

    funhtml/__init__.py 中 __all__ = ["dataframe_to_html", "DataFrame2Html"]，
    但文件里只 `from .pd2html import dataframe_to_html`，并没有把
    `DataFrame2Html` 导入到包命名空间里。所以 __all__ 里声明的名字实际上
    并不存在于 `funhtml` 顶层模块中，`from funhtml import DataFrame2Html`
    或 `from funhtml import *` 都会失败。

    这是一个真实存在的小 bug（__init__.py 导出声明与实际导入不一致），
    按照任务范围要求不在本次冒烟测试改动中修复业务代码，这里只记录并
    验证该已知行为，避免误判为测试失败。
    """
    import funhtml

    assert "DataFrame2Html" in funhtml.__all__
    assert not hasattr(funhtml, "DataFrame2Html")

    # 正确的引用方式是从子模块导入：
    from funhtml.pd2html import DataFrame2Html

    assert DataFrame2Html is not None


class _FakeDataFrame:
    """一个鸭子类型的“类 DataFrame”对象，避免为冒烟测试引入 pandas 依赖。

    DataFrame2Html 只用到了 `.columns.values` 和 `.to_dict(orient=...)`，
    并不真正依赖 pandas，所以这里用最小实现来模拟。
    """

    class _Columns:
        def __init__(self, values):
            self.values = values

    def __init__(self, records):
        self._records = records
        self.columns = self._Columns(list(records[0].keys()) if records else [])

    def to_dict(self, orient="records"):
        assert orient == "records"
        return self._records


def test_dataframe2html_basic_rendering():
    """DataFrame2Html 用简单数据构造并渲染，不应抛异常，且输出应包含数据内容。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame(
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
    )

    converter = DataFrame2Html(data)
    html_str = converter.html_str()

    assert "<table>" in html_str
    assert "Alice" in html_str
    assert "Bob" in html_str


def test_dataframe2html_skips_url_suffixed_columns():
    """列名以 `url` 结尾或在 pass_words 中的列应当被跳过（不直接渲染为文本列）。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame(
        [
            {"name": "Alice", "name:url": "http://example.com/alice"},
        ]
    )

    converter = DataFrame2Html(data)
    html_str = converter.html_str()

    # name 列的值应变成一个指向 name:url 的链接
    assert "http://example.com/alice" in html_str
    assert "Alice" in html_str


def test_dataframe_to_html_convenience_function():
    """便捷函数 dataframe_to_html 应当返回字符串并可正常工作。"""
    from funhtml import dataframe_to_html

    data = _FakeDataFrame([{"id": 1, "name": "Alice"}])
    result = dataframe_to_html(data)

    assert isinstance(result, str)
    assert "Alice" in result


def test_pyhtml_basic_tag_rendering():
    """最基本的标签构造与字符串渲染。"""
    from funhtml.pyhtml import div

    tag = div("content")
    rendered = str(tag)

    assert "<div>" in rendered
    assert "content" in rendered
    assert "</div>" in rendered


def test_pyhtml_self_closing_tag():
    """自闭合标签（如 img）应正确渲染，且带有属性。"""
    from funhtml.pyhtml import img

    rendered = str(img(src="/path/to/logo.png"))

    assert rendered.startswith("<img")
    assert 'src="/path/to/logo.png"' in rendered
    assert rendered.endswith("/>")


def test_pyhtml_html_tag_has_doctype():
    """html 标签应自动带上 DOCTYPE 前缀。"""
    from funhtml.pyhtml import body, html

    rendered = str(html(body()))

    assert rendered.startswith("<!DOCTYPE html>")
    assert "<body>" in rendered


def test_pyhtml_escapes_special_characters():
    """默认情况下，内容中的 HTML 特殊字符应当被转义。"""
    from funhtml.pyhtml import div

    rendered = str(div("<script>alert(1)</script>"))

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def test_pyhtml_nested_tags():
    """标签可以嵌套组合。"""
    from funhtml.pyhtml import div, p

    rendered = str(div(p("a paragraph")))

    assert "<div>" in rendered
    assert "<p>" in rendered
    assert "a paragraph" in rendered


def test_no_cli_entry_point_declared():
    """funhtml 的 pyproject.toml 未声明任何 [project.scripts] CLI 入口，
    因此没有可供冒烟测试的命令行工具；此测试仅确认这一点，避免遗漏。
    """
    result = subprocess.run(
        [sys.executable, "-c", "import shutil; print(shutil.which('funhtml'))"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "None"
