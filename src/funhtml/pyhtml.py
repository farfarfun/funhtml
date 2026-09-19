"""

PyHTML
======

Python 版轻量 HTML 生成器。


用法：

先创建一个标签。

>>> t = div()
>>> t
div()


标签可以通过转成字符串来渲染。

>>> str(t)
'<div></div>'


打印对象会自动调用 str()。为了清晰起见，本教程后续都用 print 打印标签。

>>> print(div())
<div></div>


标签没有内容时可以省略括号。

>>> print(div)
<div></div>


有些标签是自闭合的。
>>> print(hr)
<hr/>


可以往标签里放内容。

>>> print(div('content'))
<div>
  content
</div>


可以设置标签的属性。

>>> print(div(lang='tr', id='content', class_="bar", data_value="foo"))
<div class="bar" data-value="foo" id="content" lang="tr"></div>


也可以属性和内容一起给：

>>> print(div(lang='tr')('content'))
<div lang="tr">
  content
</div>


内容可以是任何能转换成字符串的对象。

如果内容是一个 callable，渲染时会用一个参数调用它，这个参数就是你通过
render() 传入的关键字参数组成的上下文（context）。

>>> greet = lambda ctx: 'Hello %s' % ctx.get('user', 'guest')
>>> greeting = div(greet)
>>> print(greeting)
<div>
  Hello guest
</div>
>>> print(greeting.render(user='Cenk'))
<div>
  Hello Cenk
</div>


内容也可以是一个列表。

>>> print(div(nav(), greet, hr))
<div>
  <nav></nav>
  Hello guest
  <hr/>
</div>


内容也可以是一个返回列表的 callable。

>>> items = lambda ctx: [li('a'), li('b')]
>>> print(ul(items))
<ul>
  <li>
    a
  </li>
  <li>
    b
  </li>
</ul>


内容也可以是一个生成器（generator）。

>>> def items(ctx):
...    for i in range(3):
...        yield li(i)
>>> print(ul(items))
<ul>
  <li>
    0
  </li>
  <li>
    1
  </li>
  <li>
    2
  </li>
</ul>


标签可以嵌套。

>>> print(div(div(p('a paragraph'))))
<div>
  <div>
    <p>
      a paragraph
    </p>
  </div>
</div>


部分标签自带合理的默认属性。

>>> print(form())
<form method="POST"></form>

>>> print(html())
<!DOCTYPE html>
<html></html>


完整示例：

>>> print(html(
...     head(
...         title('Awesome website'),
...         script(src="http://path.to/script.js")
...     ),
...     body(
...         header(
...             img(src='/path/to/logo.png'),
...         ),
...         div(
...             'Content here'
...         ),
...         footer(
...             hr,
...             'Copyright 2012'
...         )
...     )
... ))
<!DOCTYPE html>
<html>
  <head>
    <title>
      Awesome website
    </title>
    <script src="http://path.to/script.js" type="text/javascript"></script>
  </head>
  <body>
    <header>
      <img src="/path/to/logo.png"/>
    </header>
    <div>
      Content here
    </div>
    <footer>
      <hr/>
      Copyright 2012
    </footer>
  </body>
</html>

"""

import sys
from copy import deepcopy
from io import StringIO
from types import GeneratorType
from typing import TYPE_CHECKING, Any, Callable, Iterable

if TYPE_CHECKING:
    # 动态创建的标签类的类型桩（stub）
    # 用于帮助类型检查器识别这些运行时才注册的标签
    from typing import Protocol

    class TagProtocol(Protocol):
        def __call__(self, *children: Any, **attributes: Any) -> "Tag": ...
        def __init__(self, *children: Any, **attributes: Any) -> None: ...

    # 常规标签
    body: TagProtocol
    title: TagProtocol
    div: TagProtocol
    p: TagProtocol
    h1: TagProtocol
    h2: TagProtocol
    h3: TagProtocol
    h4: TagProtocol
    h5: TagProtocol
    h6: TagProtocol
    u: TagProtocol
    b: TagProtocol
    i: TagProtocol
    s: TagProtocol
    a: TagProtocol
    em: TagProtocol
    strong: TagProtocol
    span: TagProtocol
    font: TagProtocol
    del_: TagProtocol
    ins: TagProtocol
    ul: TagProtocol
    ol: TagProtocol
    li: TagProtocol
    dd: TagProtocol
    dt: TagProtocol
    dl: TagProtocol
    article: TagProtocol
    section: TagProtocol
    nav: TagProtocol
    aside: TagProtocol
    header: TagProtocol
    footer: TagProtocol
    audio: TagProtocol
    video: TagProtocol
    object_: TagProtocol
    embed: TagProtocol
    param: TagProtocol
    fieldset: TagProtocol
    legend: TagProtocol
    button: TagProtocol
    textarea: TagProtocol
    label: TagProtocol
    select: TagProtocol
    option: TagProtocol
    table: TagProtocol
    thead: TagProtocol
    tbody: TagProtocol
    tfoot: TagProtocol
    tr: TagProtocol
    th: TagProtocol
    td: TagProtocol
    caption: TagProtocol
    blockquote: TagProtocol
    cite: TagProtocol
    q: TagProtocol
    abbr: TagProtocol
    acronym: TagProtocol
    address: TagProtocol
    head: TagProtocol

    # 自闭合标签
    meta: TagProtocol
    link: TagProtocol
    br: TagProtocol
    hr: TagProtocol
    input_: TagProtocol
    img: TagProtocol

    # 空白敏感标签
    code: TagProtocol
    samp: TagProtocol
    pre: TagProtocol
    var: TagProtocol
    kbd: TagProtocol
    dfn: TagProtocol


# 该列表会被 register_all 函数继续扩展。
__all__ = "Tag Block Safe Var SelfClosingTag html script style form".split()

tags = (
    "head body title div p h1 h2 h3 h4 h5 h6 u b i s a em strong span "
    "font del_ ins ul ol li dd dt dl article section nav aside header "
    "footer audio video object_ embed param fieldset legend button "
    "textarea label select option table thead tbody tfoot tr th td caption "
    "blockquote cite q abbr acronym address"
)

self_closing_tags = "meta link br hr input_ img"

whitespace_sensitive_tags = "code samp pre var kbd dfn"

INDENT = 2


# 预先计算好转换表，以获得最佳性能
_ESCAPE_TRANSLATION = str.maketrans(
    {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }
)


def _escape(text: str) -> str:
    """转义 HTML 特殊字符。

    使用 str.translate() 以获得最佳性能。

    Args:
        text: 待转义的文本

    Returns:
        转义后的文本
    """
    return text.translate(_ESCAPE_TRANSLATION)


class TagMeta(type):
    """Tag 的元类。（type(Tag) == TagMeta）"""

    def __str__(cls) -> str:
        """渲染为空标签。"""
        if cls.self_closing:
            return f"<{cls.__name__}/>"
        else:
            return f"<{cls.__name__}></{cls.__name__}>"

    def __repr__(cls) -> str:
        return cls.__name__


class Tag(metaclass=TagMeta):
    """HTML 标签的基类。

    Attributes:
        safe: 为 True 时渲染内容不做转义
        self_closing: 为 True 时是自闭合标签（如 <br/>）
        whitespace_sensitive: 为 True 时原样保留空白字符
        default_attributes: 该标签类型的默认属性
        doctype: 需要前置输出的 DOCTYPE 字符串（用于 html 标签）
    """

    __slots__ = ("children", "blocks", "attributes")

    safe: bool = False  # 渲染时是否跳过转义
    self_closing: bool = False
    whitespace_sensitive: bool = False
    default_attributes: dict[str, str] = {}
    doctype: str | None = None

    def __init__(self, *children: Any, **attributes: Any) -> None:
        """用子元素和属性初始化一个标签。

        Args:
            *children: 子元素（标签、字符串、callable 等）
            **attributes: HTML 属性（如 class 冲突关键字用 class_ 表示）
        """
        _safe = attributes.pop("_safe", None)
        if _safe is not None:
            self.safe = _safe

        if self.self_closing and children:
            raise ValueError("Self closing tag can't have children")

        self.children: tuple[Any, ...] = children

        self.blocks: dict[str, list["Block"]] = {}
        self._set_blocks(children)

        # 复制默认属性，避免多个实例共享同一个可变字典
        self.attributes: dict[str, Any] = dict(self.default_attributes)
        self.attributes.update(attributes)

    def __call__(self, *children: Any, **options: Any) -> "Tag":
        if self.self_closing:
            raise ValueError("Self closing tag can't have children")

        _safe = options.pop("_safe", None)
        if _safe is not None:
            self.safe = _safe

        self.children = children
        self._set_blocks(children)
        return self

    def __repr__(self) -> str:
        if self.attributes and not self.children:
            return f"{self.name}({self._repr_attributes()})"
        elif self.children and not self.attributes:
            return f"{self.name}({self._repr_children()})"
        elif self.attributes and self.children:
            return f"{self.name}({self._repr_attributes()})({self._repr_children()})"
        else:
            return f"{self.name}()"

    def _repr_attributes(self) -> str:
        return ", ".join(f"{key}={value!r}" for key, value in self.attributes.items())

    def _repr_children(self) -> str:
        return ", ".join(repr(child) for child in self.children)

    def __str__(self) -> str:
        return self.render()

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def copy(self) -> "Tag":
        return deepcopy(self)

    def render(
        self, _out: StringIO | None = None, _indent: int = 0, **context: Any
    ) -> str:
        """将标签渲染为 HTML 字符串。

        Args:
            _out: 可选的输出流（为 None 时会新建一个）
            _indent: 当前缩进级别
            **context: 用于渲染 callable 子元素/属性的上下文

        Returns:
            渲染后的 HTML 字符串
        """
        if _out is None:
            _out = StringIO()

        indent_str = " " * _indent

        # 如果存在 doctype，先写入
        if self.doctype:
            _out.write(indent_str)
            _out.write(self.doctype)
            _out.write("\n")

        # 写入带缩进的开始标签
        _out.write(indent_str)
        _out.write(f"<{self.name}")

        self._write_attributes(_out, context)

        if self.self_closing:
            _out.write("/>")
        else:
            _out.write(">")

            if self.children:
                # 非空白敏感标签，开始标签后换行
                if not self.whitespace_sensitive:
                    _out.write("\n")

                # 以增加后的缩进写入内容
                self._write_list(self.children, _out, context, _indent + INDENT)

                if not self.whitespace_sensitive:
                    # 结束标签前换行并写入缩进
                    _out.write("\n")
                    _out.write(indent_str)

            # 写入结束标签
            _out.write(f"</{self.name}>")

        return _out.getvalue()

    def _write_list(
        self,
        items: Iterable[Any],
        out: StringIO,
        context: dict[str, Any],
        indent: int = 0,
    ) -> None:
        """将一组条目写入输出流。

        Args:
            items: 待写入的可迭代对象
            out: 输出流
            context: 渲染上下文
            indent: 当前缩进级别
        """
        first = True
        for child in items:
            # 条目之间换行（第一个条目前不换行）
            if not first and not self.whitespace_sensitive:
                out.write("\n")
            first = False

            self._write_item(child, out, context, indent)

    def _write_item(
        self, item: Any, out: StringIO, context: dict[str, Any], indent: int
    ) -> None:
        if isinstance(item, Tag):
            item.render(out, indent, **context)
        elif isinstance(item, TagMeta):
            self._write_as_string(item, out, indent, escape=False)
        elif callable(item):
            rv = item(context)
            self._write_item(rv, out, context, indent)
        elif isinstance(item, (GeneratorType, list, tuple)):
            self._write_list(item, out, context, indent)
        else:
            self._write_as_string(item, out, indent)

    def _write_as_string(
        self, s: Any, out: StringIO, indent: int, escape: bool = True
    ) -> None:
        """将一个值以字符串形式写入输出流，可选转义与缩进。

        Args:
            s: 待写入的值（会被转换成字符串）
            out: 输出流
            indent: 缩进级别
            escape: 是否转义 HTML 特殊字符
        """
        if s is None:
            s = ""
        elif not isinstance(s, str):
            s = str(s)

        if escape and not self.safe:
            s = _escape(s)

        # 按正确的缩进写入内容
        if not self.whitespace_sensitive:
            indent_str = " " * indent
            lines = s.splitlines(True)
            for line in lines:
                out.write(indent_str)
                out.write(line)
        else:
            out.write(s)

    def _write_attributes(self, out: StringIO, context: dict[str, Any]) -> None:
        """将所有标签属性写入输出流。

        Args:
            out: 输出流
            context: 用于渲染 callable 属性值的上下文
        """
        for key, value in sorted(self.attributes.items()):
            # 部分属性名（如 "class"）与 Python 关键字冲突，
            # 使用者需要以下划线结尾来规避（如 class_）。
            if key.endswith("_"):
                key = key.rstrip("_")

            # 属性名里优先用短横线而非下划线。
            key = key.replace("_", "-")

            if callable(value):
                value = value(context)

            # 处理 None 值（转换成空字符串）
            if value is None:
                value = ""
            elif not isinstance(value, str):
                value = str(value)

            # 转义属性值
            value = _escape(value)

            out.write(f' {key}="{value}"')

    def __setitem__(self, block_name: str, *children: Any) -> None:
        if block_name not in self.blocks:
            raise KeyError(f"Block '{block_name}' not found")
        for block in self.blocks[block_name]:
            block(*children)

        self._set_blocks(children, block_name=block_name)

    def _set_blocks(
        self, children: tuple[Any, ...], block_name: str | None = None
    ) -> None:
        for child in children:
            if isinstance(child, Block):
                if child.block_name == block_name:
                    self.blocks[child.block_name] = [child]
                elif child.block_name not in self.blocks:
                    self.blocks[child.block_name] = []
                self.blocks[child.block_name].append(child)
            elif isinstance(child, Tag):
                for blocks in child.blocks.values():
                    self._set_blocks(blocks, block_name=block_name)


class Block(Tag):
    """可渲染条目的列表。"""

    __slots__ = ("block_name",)

    def __init__(self, name: str | None) -> None:
        super().__init__()
        self.block_name: str | None = name
        self.children: tuple[Any, ...] = ()

    def __repr__(self) -> str:
        if not self.children:
            return f"Block({self.block_name!r})"
        else:
            return f"Block({self.block_name!r})({self._repr_children()})"

    def render(
        self, _out: StringIO | None = None, _indent: int = 0, **context: Any
    ) -> str:
        if _out is None:
            _out = StringIO()

        self._write_list(self.children, _out, context, _indent)
        return _out.getvalue()


class Safe(Block):
    """用于包裹无需转义内容的辅助类。"""

    safe: bool = True

    def __init__(self, *children: Any, **options: Any) -> None:
        super().__init__(None)
        super().__call__(*children, **options)


def Var(var: str, default: Any = None) -> Callable[[dict[str, Any]], Any]:
    """从上下文中取出变量并打印的辅助函数。

    Args:
        var: 要从上下文中获取的变量名
        default: 变量不存在时的默认值

    Returns:
        用于从上下文取值的 callable
    """
    return lambda ctx: ctx.get(var, default)


class SelfClosingTag(Tag):
    self_closing = True


class WhitespaceSensitiveTag(Tag):
    whitespace_sensitive = True


class html(Tag):
    doctype = "<!DOCTYPE html>"


class script(Tag):
    safe = True
    default_attributes = {"type": "text/javascript"}


class style(Tag):
    default_attributes = {"type": "text/css"}


class form(Tag):
    default_attributes = {"method": "POST"}


# 用于动态注册标签的模块引用
_MODULE = sys.modules[__name__]


def register_all(tags: str, parent: type) -> None:
    """根据空格分隔的标签名字符串批量注册标签。

    动态创建标签类并添加到模块命名空间中。

    Args:
        tags: 空格分隔的标签名
        parent: 这些标签的父类
    """
    for tag in tags.split():
        __all__.append(tag)
        # 以 parent 为基类创建一个新的标签类
        tag_class = type(tag, (parent,), {"name": tag.rstrip("_")})
        setattr(_MODULE, tag, tag_class)


register_all(tags, Tag)
register_all(self_closing_tags, SelfClosingTag)
register_all(whitespace_sensitive_tags, WhitespaceSensitiveTag)


def __getattr__(name: str) -> Any:
    """支持类型检查器动态访问标签。

    当某个属性找不到时会调用本函数，帮助类型检查器识别动态创建的标签。

    Args:
        name: 要获取的属性名

    Returns:
        对应的标签类（如果存在）

    Raises:
        AttributeError: 标签不存在时抛出
    """
    # 这主要是为了配合类型检查——运行时标签早已通过
    # register_all() 和 setattr() 注册完毕。
    if name in __all__:
        return getattr(_MODULE, name, None)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
