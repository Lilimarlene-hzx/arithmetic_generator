"""主程序入口：负责解析命令行参数并分发“生成题目”或“批改答案”的逻辑。"""

import argparse

from generator import generate_questions, write_questions
from grader import grade


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="小学四则运算题目生成与判题程序")
	mode = parser.add_mutually_exclusive_group(required=True)
	mode.add_argument("-r", type=int, help="数值范围，生成 0 到 r-1 的题目")
	mode.add_argument("-e", help="题目文件")
	parser.add_argument("-n", type=int, default=10, help="题目数量，默认 10")
	parser.add_argument("-a", help="答案文件，与 -e 一起使用")
	return parser


def main() -> None:
	args = build_parser().parse_args()
	if args.e:
		if not args.a:
			raise SystemExit("使用 -e 时必须同时提供 -a")
		grade(args.e, args.a)
		return
	if args.n < 0:
		raise SystemExit("-n 必须是非负整数")
	try:
		write_questions(generate_questions(args.n, args.r))
	except (ValueError, RuntimeError) as error:
		raise SystemExit(str(error))


if __name__ == "__main__":
	main()

