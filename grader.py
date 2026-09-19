"""批改模块：读取题目与答案文件，比较实际答案与标准答案，并生成成绩统计。"""

from expression import parse_expression
from fraction_utils import parse_number


def _numbered_lines(path: str) -> list[str]:
	with open(path, encoding="utf-8") as file:
		return [line.strip().split(".", 1)[1].strip() for line in file if line.strip()]


def grade(exercise_file: str, answer_file: str, output_file: str = "Grade.txt") -> tuple[list[int], list[int]]:
	exercises = _numbered_lines(exercise_file)
	answers = _numbered_lines(answer_file)
	correct, wrong = [], []
	for index, (exercise, answer) in enumerate(zip(exercises, answers), 1):
		expected = parse_expression(exercise.rstrip("=").strip()).evaluate()
		try:
			actual = parse_number(answer)
		except (ValueError, ZeroDivisionError):
			actual = None
		(correct if actual == expected else wrong).append(index)
	if len(exercises) != len(answers):
		start = min(len(exercises), len(answers)) + 1
		wrong.extend(range(start, max(len(exercises), len(answers)) + 1))

	def line(label: str, values: list[int]) -> str:
		indexes = ", ".join(map(str, values))
		return f"{label}: {len(values)} ({indexes})"

	with open(output_file, "w", encoding="utf-8") as file:
		file.write(line("Correct", correct) + "\n")
		file.write(line("Wrong", wrong) + "\n")
	return correct, wrong

