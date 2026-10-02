"""funhtml 测试套件。

覆盖公开 API 的正常路径与常见边界情况：导入、`DataFrame2Html`/
`dataframe_to_html` 的图片列、空 DataFrame、空 URL、自定义
`pass_words`，以及 `pyhtml` 的属性渲染、callable/generator 内容、
自闭合标签异常路径、`Safe`/`Var`/`Block`/`copy`/`register_all`/
callable 属性值等公开辅助能力。不测试内部私有实现细节。

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


def test_dataframe2html_exported_from_top_level():
    """`__init__.py` 中 `__all__` 声明的 `DataFrame2Html` 应当可以从顶层导入。

    历史上 `funhtml/__init__.py` 只 `from .pd2html import dataframe_to_html`，
    没有同步导入 `DataFrame2Html`，导致 `__all__` 声明与实际导出不一致，
    `from funhtml import DataFrame2Html` 会失败。已在 `__init__.py` 中补上
    该导入，这里验证修复后的行为。
    """
    import funhtml

    assert "DataFrame2Html" in funhtml.__all__
    assert hasattr(funhtml, "DataFrame2Html")

    from funhtml import DataFrame2Html

    assert DataFrame2Html is funhtml.pd2html.DataFrame2Html


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


def test_dataframe2html_renders_image_column():
    """列名命中图片关键词（如 image_url）时应渲染为 <img> 标签并带宽高参数。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame(
        [{"image_url": "http://example.com/pic.png"}],
    )

    converter = DataFrame2Html(data, image_width=100, image_height=80)
    html_str = converter.html_str()

    assert "<img" in html_str
    assert "http://example.com/pic.png?w=100&amp;h=80&amp;cp=1" in html_str


def test_dataframe2html_empty_dataframe():
    """空 DataFrame（无数据行）应仍能正常渲染出表头行，不抛异常。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame([])
    converter = DataFrame2Html(data)
    html_str = converter.html_str()

    assert "<table>" in html_str
    assert "<tr>" in html_str


def test_dataframe2html_empty_url_falls_back_to_plain_cell():
    """配对的 URL 列值为空字符串时，不应生成链接，应退化为普通文本单元格。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame(
        [{"name": "Alice", "name:url": ""}],
    )

    converter = DataFrame2Html(data)
    html_str = converter.html_str()

    assert "<a " not in html_str
    assert "Alice" in html_str


def test_dataframe2html_custom_pass_words():
    """自定义 pass_words 应能覆盖默认跳过列表。"""
    from funhtml.pd2html import DataFrame2Html

    data = _FakeDataFrame(
        [{"id": 1, "secret": "hidden", "url": "http://example.com"}],
    )

    converter = DataFrame2Html(data)
    converter.pass_words = ["secret"]
    html_str = converter.html_str()

    assert "hidden" not in html_str
    # 默认跳过词 "url" 被自定义列表覆盖后不再生效，url 列应正常渲染
    assert "http://example.com" in html_str


def test_dataframe_to_html_with_custom_pass_words_argument():
    """便捷函数 dataframe_to_html 的 pass_words 参数应生效。"""
    from funhtml import dataframe_to_html

    data = _FakeDataFrame([{"id": 1, "name": "Alice"}])
    result = dataframe_to_html(data, pass_words=["name"])

    assert "Alice" not in result
    assert "id" in result or "1" in result


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


def test_pyhtml_attribute_rendering_and_class_underscore():
    """属性按 key 排序输出，`class_`/`data_value` 等下划线写法应转换为标准属性名。"""
    from funhtml.pyhtml import div

    rendered = str(div(lang="tr", id="content", class_="bar", data_value="foo"))

    assert rendered == '<div class="bar" data-value="foo" id="content" lang="tr"></div>'


def test_pyhtml_callable_content_uses_render_context():
    """content 为 callable 时，应在 render() 传入的上下文（context）中求值。"""
    from funhtml.pyhtml import div

    def greet(ctx):
        return "Hello {}".format(ctx.get("user", "guest"))

    tag = div(greet)

    assert "Hello guest" in tag.render()
    assert "Hello Cenk" in tag.render(user="Cenk")


def test_pyhtml_generator_content():
    """content 为生成器（callable 返回 generator）时应逐项渲染。"""
    from funhtml.pyhtml import li, ul

    def items(ctx):
        for i in range(3):
            yield li(i)

    rendered = str(ul(items))

    assert rendered.count("<li>") == 3
    assert "0" in rendered and "1" in rendered and "2" in rendered


def test_pyhtml_self_closing_tag_rejects_children():
    """自闭合标签传入子元素应抛出 ValueError，而不是静默忽略。"""
    from funhtml.pyhtml import img

    try:
        img("not allowed")
    except ValueError:
        pass
    else:
        raise AssertionError("self-closing tag with children should raise ValueError")


def test_pyhtml_safe_skips_escaping():
    """`Safe` 包裹的内容渲染时不应被转义（用于已知安全的原始 HTML 片段）。"""
    from funhtml.pyhtml import Safe, div

    tag = div(Safe("<b>bold</b>"))
    rendered = str(tag)

    assert "<b>bold</b>" in rendered
    assert "&lt;b&gt;" not in rendered


def test_pyhtml_var_reads_context_with_default():
    """`Var` 应从 render() 的上下文中按变量名取值，取不到时回退到默认值。"""
    from funhtml.pyhtml import Var, div

    tag = div(Var("title", default="untitled"))

    assert "untitled" in tag.render()
    assert "My Page" in tag.render(title="My Page")


def test_pyhtml_block_replacement_via_setitem():
    """`Block` 占位块应能通过 `tag[block_name] = ...` 替换内容。"""
    from funhtml.pyhtml import Block, div, li, ul

    page = div(ul(Block("items"), li("placeholder")))
    page["items"] = li("real item")

    rendered = str(page)
    assert "real item" in rendered


def test_pyhtml_block_setitem_unknown_name_raises():
    """对不存在的 block 名赋值应抛出 KeyError，而不是静默忽略。"""
    from funhtml.pyhtml import Block, div

    page = div(Block("known"))

    try:
        page["unknown"] = "x"
    except KeyError:
        pass
    else:
        raise AssertionError("未知 block 名应抛出 KeyError")


def test_pyhtml_copy_produces_independent_deep_copy():
    """`copy()` 应返回深拷贝，修改副本的子元素不影响原对象。"""
    from funhtml.pyhtml import div, p

    original = div(p("original"))
    duplicate = original.copy()
    duplicate.children[0].children = ("changed",)

    assert "original" in str(original)
    assert "changed" in str(duplicate)
    assert duplicate is not original


def test_pyhtml_register_all_creates_new_tag_class():
    """`register_all` 应能动态创建新标签类并挂载到模块命名空间。"""
    from funhtml import pyhtml
    from funhtml.pyhtml import Tag, register_all

    assert not hasattr(pyhtml, "custom_widget")
    register_all("custom_widget", Tag)

    try:
        assert hasattr(pyhtml, "custom_widget")
        custom_widget = pyhtml.custom_widget
        assert issubclass(custom_widget, Tag)
        assert str(custom_widget("hi")) == "<custom_widget>\n  hi\n</custom_widget>"
    finally:
        # 避免污染其他测试的模块全局状态
        delattr(pyhtml, "custom_widget")
        pyhtml.__all__.remove("custom_widget")


def test_pyhtml_callable_attribute_value_uses_render_context():
    """属性值为 callable 时，应在 render() 的上下文中求值后再写入。"""
    from funhtml.pyhtml import div

    tag = div(lang=lambda ctx: ctx.get("lang", "en"))

    assert 'lang="en"' in tag.render()
    assert 'lang="zh"' in tag.render(lang="zh")


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
