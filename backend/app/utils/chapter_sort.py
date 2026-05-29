"""章节编号解析工具函数

提供章节标题编号解析相关的工具函数。
"""

import logging
import re
from typing import Tuple, Optional

from pypinyin import pinyin, Style

logger = logging.getLogger(__name__)


def get_pinyin_initial(text: str) -> str:
    """获取文本的拼音首字母

    用于无编号文件的排序。

    Args:
        text: 文本内容

    Returns:
        拼音首字母（小写）

    Examples:
        >>> get_pinyin_initial("概念")
        'g'
        >>> get_pinyin_initial("Apple")
        'a'
    """
    if not text:
        return ""

    # 获取第一个字符
    first_char = text[0]

    # 如果是英文字母，直接返回小写
    if first_char.isalpha() and ord(first_char) < 128:
        return first_char.lower()

    # 如果是中文字符，使用 pypinyin 获取拼音首字母
    try:
        result = pinyin(first_char, style=Style.FIRST_LETTER)
        return result[0][0].lower() if result else ""
    except Exception as e:
        logger.warning(f"拼音转换失败: {e}")
        return ""


def parse_title_number(title: str) -> Tuple[int, ...] | None:
    """解析文章标题编号

    解析 "X.Y 标题" 或 "X.Y.Z 标题" 格式的编号。

    Args:
        title: 章节标题

    Returns:
        编号元组（如 (1, 1) 或 (1, 1, 2)），无编号返回 None

    Examples:
        >>> parse_title_number("1.1 基础概念")
        (1, 1)
        >>> parse_title_number("10.12 高级用法")
        (10, 12)
        >>> parse_title_number("1.1.2 嵌套小节")
        (1, 1, 2)
        >>> parse_title_number("无编号文章")
        None
    """
    # 匹配开头数字编号模式（支持多级，如 1.1, 1.1.2, 10.12.3）
    pattern = r"^(\d+(?:\.\d+)+)\s+"
    match = re.match(pattern, title)

    if not match:
        return None

    # 提取编号部分
    number_str = match.group(1)
    # 按点分割并转为整数
    numbers = tuple(int(num) for num in number_str.split("."))

    return numbers


def parse_folder_number(title: str) -> int | None:
    """解析文件夹标题编号

    解析以下格式：
    - "1 基础" → 1
    - "第一章 概述" → 1
    - "第二章" → 2
    - "Chapter 1 Introduction" → 1
    - "第1节 基础" → 1
    - "Chapter 2 进阶" → 2

    Args:
        title: 文件夹标题

    Returns:
        编号数字，无编号返回 None

    Examples:
        >>> parse_folder_number("第一章 概述")
        1
        >>> parse_folder_number("第二章")
        2
        >>> parse_folder_number("Chapter 2 进阶")
        2
        >>> parse_folder_number("第1节 基础")
        1
        >>> parse_folder_number("基础概念")
        None
    """
    # 中文数字映射
    chinese_numbers = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }

    # 匹配 "第X章/节" 格式（优先匹配，支持中文数字）
    pattern2 = r"^第([一二三四五六七八九十\d]+)[章节课]"
    match = re.match(pattern2, title)
    if match:
        num_str = match.group(1)
        # 如果是中文数字
        if num_str in chinese_numbers:
            return chinese_numbers[num_str]
        # 如果是阿拉伯数字
        try:
            return int(num_str)
        except ValueError:
            pass

    # 优先匹配 "数字 标题" 格式
    pattern1 = r"^(\d+)\s+"
    match = re.match(pattern1, title)
    if match:
        return int(match.group(1))

    # 匹配 "Chapter X" 或 "Section X" 格式
    pattern3 = r"^(?:Chapter|Section)\s+(\d+)\s+"
    match = re.match(pattern3, title, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # 匹配纯数字格式（如 "1", "2"）
    pattern4 = r"^(\d+)$"
    match = re.match(pattern4, title)
    if match:
        return int(match.group(1))

    return None


def extract_sort_key(title: str, is_folder: bool = False) -> Tuple:
    """提取排序键

    根据标题提取用于排序的键值。
    无编号标题返回 (0, pinyin_initial, title) 确保排到最前。

    Args:
        title: 章节标题
        is_folder: 是否为文件夹

    Returns:
        排序键元组

    Examples:
        >>> extract_sort_key("1.1 基础概念", is_folder=False)
        (1, 1, 0)
        >>> extract_sort_key("第一章 概述", is_folder=True)
        (1, 0)
        >>> extract_sort_key("无编号文章", is_folder=False)
        (0, 'w', '无编号文章')
    """
    if is_folder:
        number = parse_folder_number(title)
        if number is not None:
            return (number, 0)
        else:
            # 无编号文件夹按拼音排序，排在最前
            pinyin_initial = get_pinyin_initial(title)
            return (0, pinyin_initial, title)
    else:
        numbers = parse_title_number(title)
        if numbers is not None:
            # 返回编号元组，末尾加 0 保持类型一致
            return numbers + (0,)
        else:
            # 无编号文章按拼音排序，排在最前
            pinyin_initial = get_pinyin_initial(title)
            return (0, pinyin_initial, title)
