"""工具导出模块：对外暴露常用的分数处理函数，方便其他模块直接导入。"""

from fraction_utils import format_fraction, parse_number

__all__ = ["format_fraction", "parse_number"]
