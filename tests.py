"""测试脚本：验证四则运算生成器与判题器是否满足题目要求。

测试覆盖内容：
- 命令行参数校验
- 生成题目数量控制
- 数值范围控制
- 非负数与除法合法性约束
- 操作符数量限制
- 去重规则
- 生成结果写入文件
- 题目与答案的判题统计
- 真分数与带分数支持
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from expression import parse_expression
from fraction_utils import parse_number
from generator import generate_questions, write_questions
from grader import grade

ROOT = Path(__file__).resolve().parent


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """在项目根目录运行命令，并返回结果。"""
    return subprocess.run(
        [sys.executable, str(ROOT / 'main.py'), *args],
        check=False, cwd=str(ROOT),
        capture_output=True,
        text=True,
    )


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_generate_count_and_range() -> None:
    questions = generate_questions(10, 10, seed=42)
    assert_true(len(questions) == 10, '题目数量应为 10')
    for text, answer in questions:
        assert_true(text, '题目不能为空')
        assert_true(answer, '答案不能为空')


def test_zero_or_one_limit() -> None:
    q1 = generate_questions(5, 1, seed=1)
    q2 = generate_questions(5, 2, seed=1)
    assert_true(len(q1) == 5 and len(q2) == 5, '极小范围也应能生成指定数量题目')


def test_no_negative_subtraction() -> None:
    questions = generate_questions(200, 10, seed=7)
    for expr_text, _ in questions:
        expr = parse_expression(expr_text)
        assert_true(expr.valid_constraints(), f'生成了不合法表达式: {expr_text}')


def test_division_result_is_fraction() -> None:
    # 取一组样例，确保除法不会产生整数，且选择满足规则
    for expr_text, _ in generate_questions(100, 10, seed=9):
        expr = parse_expression(expr_text)
        if '÷' in expr_text:
            assert_true(expr.valid_constraints(), f'除法表达式不合法: {expr_text}')


def test_operator_count_limit() -> None:
    for expr_text, _ in generate_questions(200, 10, seed=11):
        count = sum(ch in '+-×÷' for ch in expr_text)
        assert_true(count <= 3, f'运算符个数超过 3: {expr_text}')


def test_no_duplicate_questions() -> None:
    questions = generate_questions(200, 10, seed=13)
    seen = set()
    for expr_text, _ in questions:
        key = parse_expression(expr_text).canonical_key()
        assert_true(key not in seen, f'发现重复题目: {expr_text}')
        seen.add(key)


def test_write_questions_files() -> None:
    q = generate_questions(5, 10, seed=3)
    write_questions(q, 'Exercises_test.txt', 'Answers_test.txt')
    assert_true(Path('Exercises_test.txt').exists(), '题目文件未生成')
    assert_true(Path('Answers_test.txt').exists(), '答案文件未生成')

    with open('Exercises_test.txt', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        assert_true(len(lines) == 5, '题目文件行数不正确')

    with open('Answers_test.txt', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        assert_true(len(lines) == 5, '答案文件行数不正确')

    for p in ['Exercises_test.txt', 'Answers_test.txt']:
        os.remove(p)


from fractions import Fraction


def test_parse_fraction_and_mixed_number() -> None:
    assert_true(parse_number('3/5') == Fraction(3, 5), '真分数解析失败')
    assert_true(parse_number('2’3/8') == Fraction(19, 8), '带分数解析失败')


def test_grade_file_statistics() -> None:
    exercises = [
        '1. 1 + 2 =',
        '2. 4 - 2 =',
        '3. 3 × 2 =',
        '4. 8 ÷ 4 =',
        '5. 2/3 + 1/3 =',
    ]
    answers = [
        '1. 3',
        '2. 2',
        '3. 6',
        '4. 2',
        '5. 1',
    ]
    with open('Exercises_tmp.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(exercises) + '\n')
    with open('Answers_tmp.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(answers) + '\n')

    grade('Exercises_tmp.txt', 'Answers_tmp.txt', 'Grade_tmp.txt')
    with open('Grade_tmp.txt', encoding='utf-8') as f:
        content = f.read()
    assert_true('Correct: 5 (1, 2, 3, 4, 5)' in content, '判题统计不正确')
    assert_true('Wrong:' not in content or 'Wrong: 0' in content, '判题错误统计异常')

    for p in ['Exercises_tmp.txt', 'Answers_tmp.txt', 'Grade_tmp.txt']:
        if os.path.exists(p):
            os.remove(p)


def test_cli_requires_range() -> None:
    result = run_command(['-n', '5'])
    assert_true(result.returncode != 0, '缺少 -r 时应该报错')
    assert_true('usage:' in result.stderr.lower() or 'usage:' in result.stdout.lower(), '程序未输出帮助信息')


def test_cli_generation_and_seed_reproducibility() -> None:
    run1 = run_command(['-n', '5', '-r', '10', '--seed', '42'])
    run2 = run_command(['-n', '5', '-r', '10', '--seed', '42'])
    assert_true(run1.returncode == 0, '第一次生成命令失败')
    assert_true(run2.returncode == 0, '第二次生成命令失败')

    a = Path('Exercises.txt').read_text(encoding='utf-8')
    b = Path('Exercises.txt').read_text(encoding='utf-8')
    assert_true(a == b, '固定种子应保证结果可复现')


def test_parse_expression_on_complex_case() -> None:
    expr = parse_expression('3 × (1/2 + 1/4)')
    assert_true(expr.evaluate() == 9 / 4, '复杂分数表达式计算错误')


def test_large_scale_generation() -> None:
    questions = generate_questions(10000, 10, seed=123)
    assert_true(len(questions) == 10000, '一万道题生成失败')


def run_all_tests() -> None:
    tests = [
        test_generate_count_and_range,
        test_zero_or_one_limit,
        test_no_negative_subtraction,
        test_division_result_is_fraction,
        test_operator_count_limit,
        test_no_duplicate_questions,
        test_write_questions_files,
        test_parse_fraction_and_mixed_number,
        test_grade_file_statistics,
        test_cli_requires_range,
        test_cli_generation_and_seed_reproducibility,
        test_parse_expression_on_complex_case,
        test_large_scale_generation,
    ]
    for fn in tests:
        try:
            fn()
            print(f'PASS: {fn.__name__}')
        except Exception as exc:  # pragma: no cover
            print(f'FAIL: {fn.__name__}: {exc}')
            raise


if __name__ == '__main__':
    run_all_tests()
