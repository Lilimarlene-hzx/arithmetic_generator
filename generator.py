"""题目生成模块：随机生成小学四则运算题，并将题目与答案写入指定文件。"""

from __future__ import annotations

import random
from fractions import Fraction

from expression import Expression, parse_expression
from fraction_utils import format_fraction


def _leaf(limit: int, rng: random.Random) -> Expression:
	if rng.random() < 0.7 or limit < 2:
		return Expression.number(Fraction(rng.randrange(limit)))
	denominator = rng.randrange(2, limit + 1)
	numerator = rng.randrange(1, denominator)
	return Expression.number(Fraction(numerator, denominator))


def _candidate(limit: int, rng: random.Random, operators: int) -> Expression:
	if operators == 0:
		return _leaf(limit, rng)
	left_count = rng.randrange(operators)
	right_count = operators - 1 - left_count
	left = _candidate(limit, rng, left_count)
	right = _candidate(limit, rng, right_count)
	return Expression.operation(rng.choice("+-×÷"), left, right)


def generate_questions(count: int, limit: int, seed: int | None = None) -> list[tuple[str, str]]:
	if count < 0 or limit < 1:
		raise ValueError("count must be non-negative and range must be positive")
	rng = random.Random(seed)
	questions: list[tuple[str, str]] = []
	keys = set()
	attempts = 0
	max_attempts = max(1000, count * 10000)
	while len(questions) < count and attempts < max_attempts:
		attempts += 1
		expression = _candidate(limit, rng, rng.randrange(1, 4))
		if not expression.valid_constraints():
			continue
		rendered = expression.text()
		parsed = parse_expression(rendered)
		if not parsed.valid_constraints():
			continue
		key = parsed.canonical_key()
		if key in keys:
			continue
		keys.add(key)
		questions.append((rendered, format_fraction(parsed.evaluate())))
	if len(questions) != count:
		raise RuntimeError("unable to generate enough distinct questions for this range")
	return questions


def write_questions(questions: list[tuple[str, str]], exercise_file: str = "Exercises.txt", answer_file: str = "Answers.txt") -> None:
	with open(exercise_file, "w", encoding="utf-8") as exercises, open(answer_file, "w", encoding="utf-8") as answers:
		for index, (question, answer) in enumerate(questions, 1):
			exercises.write(f"{index}. {question} =\n")
			answers.write(f"{index}. {answer}\n")

