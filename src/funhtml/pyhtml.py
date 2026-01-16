"""

PyHTML
======

Simple HTML generator for Python.


Usage:

Lets create a tag.

>>> t = div()
>>> t
div()


Tags can be rendered by converting to string.

>>> str(t)
'<div></div>'


Printing an object automatically calls str() with that object.
I will keep printing tags in this tutorial for clarity.

>>> print(div())
<div></div>


Parentheses can be omitted if the tag has no content.

>>> print(div)
<div></div>


Some tags are self closing.
>>> print(hr)
<hr/>


You can put some content into the tag.
>>> print(div('content'))
<div>
  content
</div>


You can set attributes of the tag.

>>> print(div(lang='tr', id='content', class_="bar", data_value="foo"))
<div class="bar" data-value="foo" id="content" lang="tr"></div>


Or both:

>>> print(div(lang='tr')('content'))
<div lang="tr">
  content
</div>


Content can be anything which can be converted to string.

If content is a callable, it will be called with a one argument
    that is the context you pass to render() as keyword arguments.

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


You can give list of items as content.

>>> print(div(nav(), greet, hr))
<div>
  <nav></nav>
  Hello guest
  <hr/>
</div>


You can give give a callable returning a list as content.

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


You can give give a generator as content.

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


You can nest tags.

>>> print(div(div(p('a paragraph'))))
<div>
  <div>
    <p>
      a paragraph
    </p>
  </div>
</div>


Some tags have sensible defaults.

>>> print(form())
<form method="POST"></form>

>>> print(html())
<!DOCTYPE html>
<html></html>


Full example:

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
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple

if TYPE_CHECKING:
    # Type stubs for dynamically created tag classes
    # These help type checkers understand the available tags
    from typing import Protocol

    class TagProtocol(Protocol):
        def __call__(self, *children: Any, **attributes: Any) -> "Tag": ...
        def __init__(self, *children: Any, **attributes: Any) -> None: ...

    # Regular tags
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

    # Self-closing tags
    meta: TagProtocol
    link: TagProtocol
    br: TagProtocol
    hr: TagProtocol
    input_: TagProtocol
    img: TagProtocol

    # Whitespace sensitive tags
    code: TagProtocol
    samp: TagProtocol
    pre: TagProtocol
    var: TagProtocol
    kbd: TagProtocol
    dfn: TagProtocol


# The list will be extended by register_all function.
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


# Pre-compute translation table for maximum performance
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
    """Escape HTML special characters.

    Uses str.translate() for optimal performance.

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    return text.translate(_ESCAPE_TRANSLATION)


class TagMeta(type):
    """Type of the Tag. (type(Tag) == TagMeta)"""

    def __str__(cls) -> str:
        """Renders as empty tag."""
        if cls.self_closing:
            return f"<{cls.__name__}/>"
        else:
            return f"<{cls.__name__}></{cls.__name__}>"

    def __repr__(cls) -> str:
        return cls.__name__


class Tag(metaclass=TagMeta):
    """Base class for HTML tags.

    Attributes:
        safe: If True, content is not escaped while rendering
        self_closing: If True, tag is self-closing (e.g., <br/>)
        whitespace_sensitive: If True, preserve whitespace exactly
        default_attributes: Default attributes for this tag type
        doctype: DOCTYPE string to prepend (for html tag)
    """

    __slots__ = ("children", "blocks", "attributes")

    safe: bool = False  # do not escape while rendering
    self_closing: bool = False
    whitespace_sensitive: bool = False
    default_attributes: Dict[str, str] = {}
    doctype: Optional[str] = None

    def __init__(self, *children: Any, **attributes: Any) -> None:
        """Initialize a tag with optional children and attributes.

        Args:
            *children: Child elements (tags, strings, callables, etc.)
            **attributes: HTML attributes (use class_ for 'class', etc.)
        """
        _safe = attributes.pop("_safe", None)
        if _safe is not None:
            self.safe = _safe

        if self.self_closing and children:
            raise ValueError("Self closing tag can't have children")

        self.children: Tuple[Any, ...] = children

        self.blocks: Dict[str, List["Block"]] = {}
        self._set_blocks(children)

        # Copy default attributes to avoid shared mutable state
        self.attributes: Dict[str, Any] = dict(self.default_attributes)
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
        self, _out: Optional[StringIO] = None, _indent: int = 0, **context: Any
    ) -> str:
        """Render the tag to HTML string.

        Args:
            _out: Optional output stream (if None, creates new one)
            _indent: Current indentation level
            **context: Rendering context for callable children/attributes

        Returns:
            Rendered HTML string
        """
        if _out is None:
            _out = StringIO()

        indent_str = " " * _indent

        # Write doctype if present
        if self.doctype:
            _out.write(indent_str)
            _out.write(self.doctype)
            _out.write("\n")

        # Write opening tag with indentation
        _out.write(indent_str)
        _out.write(f"<{self.name}")

        self._write_attributes(_out, context)

        if self.self_closing:
            _out.write("/>")
        else:
            _out.write(">")

            if self.children:
                # Newline after opening tag (if not whitespace sensitive)
                if not self.whitespace_sensitive:
                    _out.write("\n")

                # Write content with increased indentation
                self._write_list(self.children, _out, context, _indent + INDENT)

                if not self.whitespace_sensitive:
                    # Newline and indent before closing tag
                    _out.write("\n")
                    _out.write(indent_str)

            # Write closing tag
            _out.write(f"</{self.name}>")

        return _out.getvalue()

    def _write_list(
        self,
        items: Iterable[Any],
        out: StringIO,
        context: Dict[str, Any],
        indent: int = 0,
    ) -> None:
        """Write a list of items to output.

        Args:
            items: Iterable of items to write
            out: Output stream
            context: Rendering context
            indent: Current indentation level
        """
        first = True
        for child in items:
            # Write newline between items (but not before first item)
            if not first and not self.whitespace_sensitive:
                out.write("\n")
            first = False

            self._write_item(child, out, context, indent)

    def _write_item(
        self, item: Any, out: StringIO, context: Dict[str, Any], indent: int
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
        """Write a string value to output with optional escaping and indentation.

        Args:
            s: Value to write (will be converted to string)
            out: Output stream
            indent: Indentation level
            escape: Whether to escape HTML special characters
        """
        if s is None:
            s = ""
        elif not isinstance(s, str):
            s = str(s)

        if escape and not self.safe:
            s = _escape(s)

        # Write content with proper indentation
        if not self.whitespace_sensitive:
            indent_str = " " * indent
            lines = s.splitlines(True)
            for line in lines:
                out.write(indent_str)
                out.write(line)
        else:
            out.write(s)

    def _write_attributes(self, out: StringIO, context: Dict[str, Any]) -> None:
        """Write all tag attributes to output.

        Args:
            out: Output stream
            context: Rendering context for callable values
        """
        for key, value in sorted(self.attributes.items()):
            # Some attribute names such as "class" conflict
            # with reserved keywords in Python. These must
            # be postfixed with underscore by user.
            if key.endswith("_"):
                key = key.rstrip("_")

            # Dash is preferred to underscore in attribute names.
            key = key.replace("_", "-")

            if callable(value):
                value = value(context)

            # Handle None values (convert to empty string)
            if value is None:
                value = ""
            elif not isinstance(value, str):
                value = str(value)

            # Escape attribute value
            value = _escape(value)

            out.write(f' {key}="{value}"')

    def __setitem__(self, block_name: str, *children: Any) -> None:
        if block_name not in self.blocks:
            raise KeyError(f"Block '{block_name}' not found")
        for block in self.blocks[block_name]:
            block(*children)

        self._set_blocks(children, block_name=block_name)

    def _set_blocks(
        self, children: Tuple[Any, ...], block_name: Optional[str] = None
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
    """List of renderable items."""

    __slots__ = ("block_name",)

    def __init__(self, name: Optional[str]) -> None:
        super().__init__()
        self.block_name: Optional[str] = name
        self.children: Tuple[Any, ...] = ()

    def __repr__(self) -> str:
        if not self.children:
            return f"Block({self.block_name!r})"
        else:
            return f"Block({self.block_name!r})({self._repr_children()})"

    def render(
        self, _out: Optional[StringIO] = None, _indent: int = 0, **context: Any
    ) -> str:
        if _out is None:
            _out = StringIO()

        self._write_list(self.children, _out, context, _indent)
        return _out.getvalue()


class Safe(Block):
    """Helper for wrapping content that do not need escaping."""

    safe: bool = True

    def __init__(self, *children: Any, **options: Any) -> None:
        super().__init__(None)
        super().__call__(*children, **options)


def Var(var: str, default: Any = None) -> Callable[[Dict[str, Any]], Any]:
    """Helper function for printing a variable from context.

    Args:
        var: Variable name to get from context
        default: Default value if variable not found

    Returns:
        Callable that retrieves the variable from context
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


# Module reference for dynamic tag registration
_MODULE = sys.modules[__name__]


def register_all(tags: str, parent: type) -> None:
    """Register all tags from a space-separated string.

    Dynamically creates tag classes and adds them to the module namespace.

    Args:
        tags: Space-separated tag names
        parent: Parent class for the tags
    """
    for tag in tags.split():
        __all__.append(tag)
        # Create a new class for this tag with the parent as base
        tag_class = type(tag, (parent,), {"name": tag.rstrip("_")})
        setattr(_MODULE, tag, tag_class)


register_all(tags, Tag)
register_all(self_closing_tags, SelfClosingTag)
register_all(whitespace_sensitive_tags, WhitespaceSensitiveTag)


def __getattr__(name: str) -> Any:
    """Support dynamic tag access for type checkers.

    This function is called when an attribute is not found,
    which helps type checkers understand dynamically created tags.

    Args:
        name: Name of the attribute to get

    Returns:
        The tag class if it exists

    Raises:
        AttributeError: If the tag doesn't exist
    """
    # This is mainly for type checking - at runtime, tags are already
    # registered via register_all() and setattr()
    if name in __all__:
        return getattr(_MODULE, name, None)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
