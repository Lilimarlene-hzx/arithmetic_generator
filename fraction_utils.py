"""分数工具模块：负责分数的解析、格式化，以及与字符串之间的相互转换。"""

import re
from fractions import Fraction


def parse_number(text: str) -> Fraction:
	"""Parse natural, proper, or mixed numbers used by the exercise format."""
	text = text.strip().replace("'", "’")
	if "’" in text:
		whole, fraction = text.split("’", 1)
		numerator, denominator = fraction.split("/", 1)
		return Fraction(int(whole)) + Fraction(int(numerator), int(denominator))
	if "/" in text:
		numerator, denominator = text.split("/", 1)
		return Fraction(int(numerator), int(denominator))
	if not re.fullmatch(r"\d+", text):
		raise ValueError(f"invalid number: {text}")
	return Fraction(int(text))


def format_fraction(value: Fraction) -> str:
	value = Fraction(value)
	if value.denominator == 1:
		return str(value.numerator)
	if value.numerator > value.denominator:
		whole, remainder = divmod(value.numerator, value.denominator)
		return f"{whole}’{remainder}/{value.denominator}"
	return f"{value.numerator}/{value.denominator}"

