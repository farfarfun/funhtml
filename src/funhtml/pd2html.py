from typing import Any, ClassVar

from funhtml.pyhtml import Tag, a, body, html, img, li, table, td, tr


class DataFrame2Html:
    """将 pandas DataFrame 转换为 HTML 表格。

    支持自动识别 URL 列（列名以 `:url` 结尾，或存在 `<列名>:url` 的配对列）
    并渲染为超链接；列名命中 `IMAGE_KEYWORDS` 关键词时渲染为 `<img>` 标签；
    列名在 `pass_words`（默认 `["url"]`）中的列会被整体跳过。
    """

    # 默认跳过的列名
    DEFAULT_PASS_WORDS: ClassVar[list[str]] = ["url"]
    # 图片列名关键词
    IMAGE_KEYWORDS: ClassVar[tuple[str, ...]] = ("img", "image", "pic", "image_url")
    # URL 后缀标识
    URL_SUFFIX = ":url"

    def __init__(
        self,
        data: Any,
        image_width: int = 250,
        image_height: int = 250,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """初始化转换器。

        Args:
            data: 具有 `.columns.values` 与 `.to_dict(orient=...)` 接口的
                类 DataFrame 对象（通常为 `pandas.DataFrame`）
            image_width: 图片列渲染时的显示宽度（像素）
            image_height: 图片列渲染时的显示高度（像素）
            *args: 预留位，当前未使用
            **kwargs: 预留位，当前未使用
        """
        self.data = data
        self.columns = data.columns.values
        self.data_dict = data.to_dict(orient="records")

        self.pass_words = self.DEFAULT_PASS_WORDS.copy()
        self.image_width = image_width
        self.image_height = image_height

    def __check_pass(self, col: str | None) -> bool:
        """检查列是否应该被跳过"""
        if col is None:
            return True
        if col in self.pass_words:
            return True
        return bool(col.endswith(self.URL_SUFFIX))

    def __is_image_column(self, col: str) -> bool:
        """检查列是否为图片列"""
        col_lower = col.lower()
        return col_lower in self.IMAGE_KEYWORDS or any(
            keyword in col_lower for keyword in self.IMAGE_KEYWORDS
        )

    def __build_image_url(self, image_url: str) -> str:
        """构建带参数的图片 URL"""
        image_property = f"w={self.image_width}&h={self.image_height}&cp=1"
        if "?" in image_url:
            return f"{image_url}&{image_property}"
        return f"{image_url}?{image_property}"

    def get_title(self) -> Tag:
        """生成表头行。

        Returns:
            包含所有未被跳过列名的 `<tr>` 标签
        """
        tds = [td(col) for col in self.columns if not self.__check_pass(col)]
        return tr(tds)

    def get_td(self, col: str, data_dict: dict) -> Tag | None:
        """生成单个单元格。

        Args:
            col: 列名
            data_dict: 当前行数据（列名到值的映射）

        Returns:
            渲染后的 `<td>` 标签；列被跳过时返回 None。存在 `<列名>:url`
            配对列时渲染为超链接，图片列渲染为 `<img>`，其余为普通文本
        """
        if self.__check_pass(col):
            return None

        data = data_dict.get(col)
        col_url = f"{col}{self.URL_SUFFIX}"

        # 如果存在对应的 URL 列，生成链接
        if col_url in data_dict:
            url = data_dict[col_url]
            if url:  # 确保 URL 不为空
                return td(li(a(href=url, target="_blank")(data)))

        # 如果是图片列，生成图片标签
        if self.__is_image_column(col) and data:
            image_url = str(data)
            path = self.__build_image_url(image_url)
            return td(img(src=path))

        # 普通数据列
        return td(data)

    def get_tr(self, data: dict) -> Tag:
        """生成一行数据。

        Args:
            data: 单行数据（列名到值的映射）

        Returns:
            包含该行所有未被跳过单元格的 `<tr>` 标签
        """
        tds = []
        for col in self.columns:
            td_element = self.get_td(col, data)
            if td_element is not None:
                tds.append(td_element)
        return tr(tds)

    def html(self) -> Tag:
        """生成完整的 HTML 标签结构。

        Returns:
            `html(body(table(...)))` 结构的根标签，表格首行为表头，
            其余为数据行
        """
        trs = [self.get_title()]
        trs.extend(self.get_tr(d) for d in self.data_dict)
        return html(body(table(trs)))

    def html_str(self) -> str:
        """生成 HTML 字符串。

        Returns:
            `html()` 渲染后的完整 HTML 文本（含 DOCTYPE）
        """
        return self.html().render()


def dataframe_to_html(
    df: Any,
    image_width: int = 250,
    image_height: int = 250,
    pass_words: list[str] | None = None,
) -> str:
    """将 pandas DataFrame 转换为 HTML 字符串

    这是一个便捷函数，用于快速将 pandas DataFrame 转换为 HTML 字符串。
    支持自动识别图片列、URL 链接等功能。

    Args:
        df: pandas DataFrame 对象
        image_width: 图片显示宽度（像素），默认 250
        image_height: 图片显示高度（像素），默认 250
        pass_words: 要跳过的列名列表，如果为 None 则使用默认值 ["url"]

    Returns:
        HTML 字符串

    Examples:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
        >>> html_str = dataframe_to_html(df)  # 获取 HTML 字符串
        >>> print(html_str)  # 打印或保存到文件
    """
    # 创建 DataFrame2Html 实例
    converter = DataFrame2Html(df, image_width=image_width, image_height=image_height)

    # 如果指定了自定义的 pass_words，更新它
    if pass_words is not None:
        converter.pass_words = pass_words

    return converter.html_str()
