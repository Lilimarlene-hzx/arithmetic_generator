"""表达式解析与计算模块：把算式文本转成表达式树，支持计算、优先级和合法性校验。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from xxlimited import Str

from fraction_utils import format_fraction, parse_number

OPERATORS = "+-×÷"


@dataclass(frozen=True)
class Expression:
	value: Fraction | None = None
	operator: Str | None = None
	left: Expression | None = None
	right: Expression | None = None

	@classmethod
	def number(cls, value: Fraction) -> Expression:
		return cls(value=Fraction(value))

	@classmethod
	def operation(cls, operator: str, left: Expression, right: Expression) -> Expression:
		return cls(operator=operator, left=left, right=right)

	@property
	def is_number(self) -> bool:
		return self.operator is None

	def evaluate(self) -> Fraction:
		if self.is_number:
			return self.value  # type: ignore[return-value]
		left = self.left.evaluate()  # type: ignore[union-attr]
		right = self.right.evaluate()  # type: ignore[union-attr]
		if self.operator == "+":
			return left + right
		if self.operator == "-":
			return left - right
		if self.operator == "×":
			return left * right
		if right == 0:
			raise ZeroDivisionError
		return left / right

	def operator_count(self) -> int:
		if self.is_number:
			return 0
		return 1 + self.left.operator_count() + self.right.operator_count()  # type: ignore[union-attr]

	def valid_constraints(self) -> bool:
		if self.is_number:
			return True
		if not self.left.valid_constraints() or not self.right.valid_constraints():  # type: ignore[union-attr]
			return False
		left = self.left.evaluate()  # type: ignore[union-attr]
		right = self.right.evaluate()  # type: ignore[union-attr]
		if self.operator == "-" and left < right:
			return False
		return self.operator != "÷" or (right != 0 and left < right)

	def text(self, parent_precedence: int = 0) -> str:
		if self.is_number:
			return format_fraction(self.value)  # type: ignore[arg-type]
		precedence = 1 if self.operator in "+-" else 2
		left_text = self.left.text(precedence)  # type: ignore[union-attr]
		right_text = self.right.text(precedence)  # type: ignore[union-attr]
		right_operator = self.right.operator  # type: ignore[union-attr]
		if right_operator is not None and (
			self.operator in "-÷" or (self.operator == "×" and right_operator == "÷")
		) and (1 if right_operator in "+-" else 2) == precedence:
			right_text = f"({self.right.text()})"  # type: ignore[union-attr]
		rendered = f"{left_text} {self.operator} {right_text}"
		if precedence < parent_precedence:
			return f"({rendered})"
		return rendered

	def canonical_key(self):
		if self.is_number:
			return ("number", self.value.numerator, self.value.denominator)  # type: ignore[union-attr]
		left = self.left.canonical_key()  # type: ignore[union-attr]
		right = self.right.canonical_key()  # type: ignore[union-attr]
		if self.operator in "+×":
			left, right = sorted((left, right), key=repr)
		return (self.operator, left, right)


class _Parser:
	def __init__(self, text: str):
		self.tokens = re.findall(r"\d+|[’'/]|[()+\-×÷]", text.replace("=", " "))
		self.tokens = self._combine_number_tokens()
		self.position = 0

	def _combine_number_tokens(self) -> list[str]:
		combined = []
		index = 0
		while index < len(self.tokens):
			token = self.tokens[index]
			if token.isdigit() and index + 2 < len(self.tokens) and self.tokens[index + 1] == "/" and self.tokens[index + 2].isdigit():
				token += "/" + self.tokens[index + 2]
				index += 3
			elif token.isdigit() and index + 4 < len(self.tokens) and self.tokens[index + 1] in ("’", "'") and self.tokens[index + 2].isdigit() and self.tokens[index + 3] == "/" and self.tokens[index + 4].isdigit():
				token += "’" + self.tokens[index + 2] + "/" + self.tokens[index + 4]
				index += 5
			else:
				index += 1
			combined.append(token)
		return combined

	def current(self):
		return self.tokens[self.position] if self.position < len(self.tokens) else None

	def take(self, token=None):
		current = self.current()
		if token is not None and current != token:
			raise ValueError("unexpected token")
		self.position += 1
		return current

	def parse(self) -> Expression:
		result = self.parse_additive()
		if self.current() is not None:
			raise ValueError("unexpected trailing token")
		return result

	def parse_additive(self) -> Expression:
		result = self.parse_multiplicative()
		while self.current() in ("+", "-"):
			operator = self.take()
			result = Expression.operation(operator, result, self.parse_multiplicative())
		return result

	def parse_multiplicative(self) -> Expression:
		result = self.parse_primary()
		while self.current() in ("×", "÷"):
			operator = self.take()
			result = Expression.operation(operator, result, self.parse_primary())
		return result

	def parse_primary(self) -> Expression:
		if self.current() == "(":
			self.take("(")
			result = self.parse_additive()
			self.take(")")
			return result
		token = self.take()
		if token is None or token in OPERATORS or token in ")":
			raise ValueError("number expected")
		return Expression.number(parse_number(token))


def parse_expression(text: str) -> Expression:
	return _Parser(text.strip()).parse()

