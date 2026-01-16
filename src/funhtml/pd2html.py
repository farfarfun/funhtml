from typing import Any, Dict, List, Optional

from funhtml.pyhtml import a, body, html, img, li, table, td, tr


class DataFrame2Html:
    # 默认跳过的列名
    DEFAULT_PASS_WORDS = ["url"]
    # 图片列名关键词
    IMAGE_KEYWORDS = ("img", "image", "pic", "image_url")
    # URL 后缀标识
    URL_SUFFIX = ":url"

    def __init__(
        self, data, image_width: int = 250, image_height: int = 250, *args, **kwargs
    ):
        self.data = data
        self.columns = data.columns.values
        self.data_dict = data.to_dict(orient="records")

        self.pass_words = self.DEFAULT_PASS_WORDS.copy()
        self.image_width = image_width
        self.image_height = image_height

    def __check_pass(self, col: Optional[str]) -> bool:
        """检查列是否应该被跳过"""
        if col is None:
            return True
        if col in self.pass_words:
            return True
        if col.endswith(self.URL_SUFFIX):
            return True
        return False

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

    def get_title(self):
        """生成表头行"""
        tds = [td(col) for col in self.columns if not self.__check_pass(col)]
        return tr(tds)

    def get_td(self, col: str, data_dict: Dict) -> Optional[td]:
        """生成单个单元格"""
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

    def get_tr(self, data: Dict):
        """生成数据行"""
        tds = []
        for col in self.columns:
            td_element = self.get_td(col, data)
            if td_element is not None:
                tds.append(td_element)
        return tr(tds)

    def html(self):
        """生成 HTML 结构"""
        trs = [self.get_title()]
        trs.extend(self.get_tr(d) for d in self.data_dict)
        return html(body(table(trs)))

    def html_str(self) -> str:
        """生成 HTML 字符串"""
        return self.html().render()


def dataframe_to_html(
    df: Any,
    image_width: int = 250,
    image_height: int = 250,
    pass_words: Optional[List[str]] = None,
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
        >>> html_str = df_to_html(df)  # 获取 HTML 字符串
        >>> print(html_str)  # 打印或保存到文件
    """
    # 创建 DataFrame2Html 实例
    converter = DataFrame2Html(df, image_width=image_width, image_height=image_height)

    # 如果指定了自定义的 pass_words，更新它
    if pass_words is not None:
        converter.pass_words = pass_words

    return converter.html_str()
