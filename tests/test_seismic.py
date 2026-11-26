"""seismic 的单元测试，仅使用标准库 unittest。"""

import html.parser
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import List, Optional, Tuple

from seismic import (
    P_WAVE_SPEED,
    S_WAVE_SPEED,
    __version__,
    energy_ratio,
    epicenter_distance,
    make_questions,
    normalize_wave,
    render_demo,
    render_sheet,
    travel_time,
    wave_lag,
    write_output,
)
from seismic.cli import build_parser, main
from seismic.core import to_float
from seismic.sheet import Question, to_int


class _TagCollector(html.parser.HTMLParser):
    """收集 HTML 起始标签，用于确认页面结构可被解析。"""

    def __init__(self) -> None:
        super().__init__()
        self.tags: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.tags.append(tag)


def _parse_html(text: str) -> _TagCollector:
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector


def _run_cli(args: List[str]) -> Tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


class TestConstants(unittest.TestCase):
    def test_wave_speeds(self) -> None:
        self.assertAlmostEqual(P_WAVE_SPEED, 6.0)
        self.assertAlmostEqual(S_WAVE_SPEED, 3.5)

    def test_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")


class TestToFloat(unittest.TestCase):
    def test_accepts_int(self) -> None:
        self.assertEqual(to_float(7, "数值"), 7.0)

    def test_accepts_float(self) -> None:
        self.assertEqual(to_float(2.5, "数值"), 2.5)

    def test_accepts_numeric_string_with_spaces(self) -> None:
        self.assertEqual(to_float("  12.5 ", "数值"), 12.5)

    def test_rejects_bool(self) -> None:
        with self.assertRaises(ValueError):
            to_float(True, "数值")

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(ValueError):
            to_float("", "数值")

    def test_rejects_blank_string(self) -> None:
        with self.assertRaises(ValueError):
            to_float("   ", "数值")

    def test_rejects_text(self) -> None:
        with self.assertRaises(ValueError):
            to_float("abc", "数值")

    def test_rejects_nan_string(self) -> None:
        with self.assertRaises(ValueError):
            to_float("nan", "数值")

    def test_rejects_inf(self) -> None:
        with self.assertRaises(ValueError):
            to_float(float("inf"), "数值")

    def test_rejects_none(self) -> None:
        with self.assertRaises(ValueError):
            to_float(None, "数值")

    def test_rejects_huge_int(self) -> None:
        with self.assertRaises(ValueError):
            to_float(10 ** 400, "数值")


class TestToInt(unittest.TestCase):
    def test_accepts_int(self) -> None:
        self.assertEqual(to_int(8, "题数"), 8)

    def test_accepts_integral_float(self) -> None:
        self.assertEqual(to_int(8.0, "题数"), 8)

    def test_rejects_fractional_float(self) -> None:
        with self.assertRaises(ValueError):
            to_int(8.5, "题数")

    def test_rejects_bool(self) -> None:
        with self.assertRaises(ValueError):
            to_int(False, "题数")

    def test_accepts_digit_string(self) -> None:
        self.assertEqual(to_int(" 12 ", "题数"), 12)

    def test_rejects_text(self) -> None:
        with self.assertRaises(ValueError):
            to_int("八", "题数")

    def test_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            to_int("", "题数")

    def test_rejects_none(self) -> None:
        with self.assertRaises(ValueError):
            to_int(None, "题数")


class TestEpicenterDistance(unittest.TestCase):
    def test_known_value(self) -> None:
        self.assertAlmostEqual(epicenter_distance(5.0), 42.0, places=6)

    def test_accepts_string(self) -> None:
        self.assertAlmostEqual(epicenter_distance("5"), 42.0, places=6)

    def test_zero_lag_rejected(self) -> None:
        with self.assertRaises(ValueError):
            epicenter_distance(0.0)

    def test_negative_lag_rejected(self) -> None:
        with self.assertRaises(ValueError):
            epicenter_distance(-1.0)

    def test_lag_limit_rejected(self) -> None:
        with self.assertRaises(ValueError):
            epicenter_distance(3600.0)

    def test_lag_just_below_limit(self) -> None:
        value = epicenter_distance(3599.9)
        self.assertAlmostEqual(value, 3599.9 * 8.4, places=4)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            epicenter_distance(True)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            epicenter_distance(float("nan"))

    def test_grows_with_lag(self) -> None:
        self.assertLess(epicenter_distance(2.0), epicenter_distance(4.0))


class TestWaveLag(unittest.TestCase):
    def test_known_value(self) -> None:
        self.assertAlmostEqual(wave_lag(70.0), 175.0 / 21.0, places=6)

    def test_accepts_string(self) -> None:
        self.assertAlmostEqual(wave_lag("70"), 175.0 / 21.0, places=6)

    def test_zero_distance_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wave_lag(0.0)

    def test_negative_distance_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wave_lag(-5.0)

    def test_distance_limit_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wave_lag(20000.0)

    def test_distance_just_below_limit(self) -> None:
        value = wave_lag(19999.0)
        self.assertAlmostEqual(value, 19999.0 * 2.5 / 21.0, places=4)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wave_lag(True)

    def test_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            wave_lag(float("inf"))

    def test_round_trip(self) -> None:
        self.assertAlmostEqual(wave_lag(epicenter_distance(5.0)), 5.0, places=6)


class TestTravelTime(unittest.TestCase):
    def test_p_wave(self) -> None:
        self.assertAlmostEqual(travel_time(100.0, "p"), 100.0 / 6.0, places=6)

    def test_s_wave(self) -> None:
        self.assertAlmostEqual(travel_time(100.0, "s"), 100.0 / 3.5, places=6)

    def test_uppercase_wave(self) -> None:
        self.assertAlmostEqual(travel_time(60.0, "P"), 10.0, places=6)

    def test_wave_with_spaces(self) -> None:
        self.assertAlmostEqual(travel_time(35.0, " s "), 10.0, places=6)

    def test_invalid_wave(self) -> None:
        with self.assertRaises(ValueError):
            travel_time(100.0, "x")

    def test_empty_wave(self) -> None:
        with self.assertRaises(ValueError):
            travel_time(100.0, "")

    def test_non_string_wave(self) -> None:
        with self.assertRaises(ValueError):
            travel_time(100.0, None)

    def test_zero_distance(self) -> None:
        with self.assertRaises(ValueError):
            travel_time(0.0, "p")

    def test_distance_limit(self) -> None:
        with self.assertRaises(ValueError):
            travel_time(20000.0, "p")

    def test_p_faster_than_s(self) -> None:
        self.assertLess(travel_time(200.0, "p"), travel_time(200.0, "s"))


class TestEnergyRatio(unittest.TestCase):
    def test_known_value(self) -> None:
        self.assertAlmostEqual(energy_ratio(5.0, 7.0), 1000.0, places=6)

    def test_equal_magnitude(self) -> None:
        self.assertAlmostEqual(energy_ratio(3.0, 3.0), 1.0, places=9)

    def test_accepts_strings(self) -> None:
        self.assertAlmostEqual(energy_ratio("5", "7"), 1000.0, places=6)

    def test_reversed_magnitude_rejected(self) -> None:
        with self.assertRaises(ValueError):
            energy_ratio(7.0, 5.0)

    def test_negative_magnitude_rejected(self) -> None:
        with self.assertRaises(ValueError):
            energy_ratio(-0.1, 3.0)

    def test_over_max_magnitude_rejected(self) -> None:
        with self.assertRaises(ValueError):
            energy_ratio(0.0, 10.0)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            energy_ratio(True, 3.0)

    def test_largest_range_is_finite(self) -> None:
        value = energy_ratio(0.0, 9.9)
        self.assertTrue(value < 1e15)
        self.assertTrue(value > 0.0)


class TestNormalizeWave(unittest.TestCase):
    def test_uppercase(self) -> None:
        self.assertEqual(normalize_wave("P"), "p")

    def test_spaces(self) -> None:
        self.assertEqual(normalize_wave(" s "), "s")

    def test_chinese_label_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_wave("P波")

    def test_none_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_wave(None)


class TestMakeQuestions(unittest.TestCase):
    def test_length_matches_count(self) -> None:
        self.assertEqual(len(make_questions(1, 1)), 1)
        self.assertEqual(len(make_questions(8, 1)), 8)
        self.assertEqual(len(make_questions(50, 1)), 50)

    def test_count_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(0, 1)

    def test_count_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_count_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(True, 1)

    def test_count_text_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions("八", 1)

    def test_same_seed_reproducible(self) -> None:
        self.assertEqual(make_questions(6, 3), make_questions(6, 3))

    def test_different_seed_differs(self) -> None:
        self.assertNotEqual(make_questions(6, 3), make_questions(6, 4))

    def test_numbering_starts_at_one(self) -> None:
        questions = make_questions(5, 9)
        self.assertEqual([item.number for item in questions], [1, 2, 3, 4, 5])

    def test_all_kinds_covered(self) -> None:
        kinds = {item.kind for item in make_questions(8, 1)}
        self.assertEqual(kinds, {"震中距", "到时差", "走时", "能量倍数"})

    def test_fields_are_filled(self) -> None:
        for item in make_questions(8, 2):
            self.assertIsInstance(item, Question)
            self.assertTrue(item.prompt)
            self.assertTrue(item.answer)
            self.assertTrue(item.working)

    def test_first_question_is_distance(self) -> None:
        self.assertEqual(make_questions(1, 1)[0].kind, "震中距")

    def test_seed_zero_allowed(self) -> None:
        self.assertEqual(len(make_questions(3, 0)), 3)


class TestRenderSheet(unittest.TestCase):
    def setUp(self) -> None:
        self.questions = make_questions(4, 5)

    def test_doctype(self) -> None:
        self.assertTrue(render_sheet(self.questions).startswith("<!DOCTYPE html>"))

    def test_question_count_in_html(self) -> None:
        page = render_sheet(self.questions)
        self.assertEqual(page.count("<li>"), 4)

    def test_no_answers_by_default(self) -> None:
        page = render_sheet(self.questions)
        self.assertNotIn("答案：", page)
        self.assertNotIn('class="working"', page)

    def test_answers_included(self) -> None:
        page = render_sheet(self.questions, True)
        self.assertIn("答案：", page)
        self.assertIn('class="working"', page)

    def test_parsable_by_html_parser(self) -> None:
        tags = _parse_html(render_sheet(self.questions)).tags
        self.assertIn("html", tags)
        self.assertIn("ol", tags)
        self.assertIn("main", tags)
        self.assertEqual(tags.count("li"), 4)

    def test_text_is_escaped(self) -> None:
        risky = Question(1, "测试", "<script>alert(1)</script>", "1", "过程")
        page = render_sheet([risky], True)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_empty_list_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet([])

    def test_none_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(None)

    def test_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet("abc")

    def test_contains_tips(self) -> None:
        self.assertIn("P 波速度 6.0 千米/秒", render_sheet(self.questions))


class TestRenderDemo(unittest.TestCase):
    def test_contains_svg(self) -> None:
        self.assertIn("<svg", render_demo())

    def test_contains_wave_labels(self) -> None:
        page = render_demo()
        self.assertIn("P 波", page)
        self.assertIn("S 波", page)

    def test_contains_energy_formula(self) -> None:
        self.assertIn("10^(1.5", render_demo())

    def test_parsable_by_html_parser(self) -> None:
        tags = _parse_html(render_demo()).tags
        self.assertIn("svg", tags)
        self.assertIn("section", tags)

    def test_starts_with_doctype(self) -> None:
        self.assertTrue(render_demo().startswith("<!DOCTYPE html>"))


class TestWriteOutput(unittest.TestCase):
    def test_writes_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "页面.html")
            write_output(path, "地震波")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "地震波")

    def test_empty_path_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_output("  ", "内容")

    def test_non_string_path_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_output(None, "内容")

    def test_missing_directory_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "no_such_dir", "x.html")
            with self.assertRaises(ValueError) as ctx:
                write_output(path, "内容")
            self.assertIn("写入文件失败", str(ctx.exception))

    def test_directory_path_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                write_output(tmp, "内容")


class TestCliCalculations(unittest.TestCase):
    def test_distance(self) -> None:
        code, out, err = _run_cli(["distance", "--lag", "5"])
        self.assertEqual(code, 0)
        self.assertIn("42.0", out)
        self.assertEqual(err, "")

    def test_lag(self) -> None:
        code, out, err = _run_cli(["lag", "--distance", "70"])
        self.assertEqual(code, 0)
        self.assertIn("8.33", out)
        self.assertEqual(err, "")

    def test_travel_p(self) -> None:
        code, out, _ = _run_cli(["travel", "--distance", "100", "--wave", "p"])
        self.assertEqual(code, 0)
        self.assertIn("P 波走时", out)
        self.assertIn("16.67", out)

    def test_travel_s(self) -> None:
        code, out, _ = _run_cli(["travel", "--distance", "100", "--wave", "S"])
        self.assertEqual(code, 0)
        self.assertIn("S 波走时", out)
        self.assertIn("28.57", out)

    def test_travel_default_wave(self) -> None:
        code, out, _ = _run_cli(["travel", "--distance", "60"])
        self.assertEqual(code, 0)
        self.assertIn("10.00", out)

    def test_energy(self) -> None:
        code, out, _ = _run_cli(["energy", "--m1", "5", "--m2", "7"])
        self.assertEqual(code, 0)
        self.assertIn("1000.0", out)

    def test_version_flag(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("0.1.0", out.getvalue())


class TestCliSheetAndDemo(unittest.TestCase):
    def test_sheet_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            code, out, err = _run_cli(
                ["sheet", "--count", "4", "--seed", "2", "-o", path]
            )
            self.assertEqual(code, 0)
            self.assertEqual(err, "")
            self.assertIn("已生成练习纸", out)
            with open(path, encoding="utf-8") as handle:
                content = handle.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertNotIn("答案：", content)

    def test_sheet_with_answers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "answers.html")
            code, out, _ = _run_cli(
                ["sheet", "--count", "4", "--seed", "2", "-o", path, "--answers"]
            )
            self.assertEqual(code, 0)
            self.assertIn("含", out)
            with open(path, encoding="utf-8") as handle:
                self.assertIn("答案：", handle.read())

    def test_sheet_seed_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = os.path.join(tmp, "a.html")
            second = os.path.join(tmp, "b.html")
            _run_cli(["sheet", "--count", "6", "--seed", "7", "-o", first])
            _run_cli(["sheet", "--count", "6", "--seed", "7", "-o", second])
            with open(first, encoding="utf-8") as handle:
                text_a = handle.read()
            with open(second, encoding="utf-8") as handle:
                text_b = handle.read()
            self.assertEqual(text_a, text_b)

    def test_demo_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "demo.html")
            code, out, err = _run_cli(["demo", "-o", path])
            self.assertEqual(code, 0)
            self.assertEqual(err, "")
            self.assertIn("已生成演示页", out)
            with open(path, encoding="utf-8") as handle:
                self.assertIn("<svg", handle.read())


class TestCliErrors(unittest.TestCase):
    def _assert_error(self, args: List[str]) -> str:
        code, out, err = _run_cli(args)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("错误：", err)
        return err

    def test_distance_text(self) -> None:
        self._assert_error(["distance", "--lag", "abc"])

    def test_distance_zero(self) -> None:
        self._assert_error(["distance", "--lag", "0"])

    def test_distance_nan(self) -> None:
        self._assert_error(["distance", "--lag", "nan"])

    def test_lag_out_of_range(self) -> None:
        self._assert_error(["lag", "--distance", "20000"])

    def test_lag_negative(self) -> None:
        self._assert_error(["lag", "--distance", "-1"])

    def test_energy_reversed(self) -> None:
        self._assert_error(["energy", "--m1", "7", "--m2", "5"])

    def test_energy_out_of_range(self) -> None:
        self._assert_error(["energy", "--m1", "0", "--m2", "12"])

    def test_travel_bad_wave(self) -> None:
        self._assert_error(["travel", "--distance", "100", "--wave", "x"])

    def test_sheet_bad_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "sheet.html")
            self._assert_error(["sheet", "--count", "0", "-o", path])

    def test_sheet_unwritable_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing", "sheet.html")
            self._assert_error(["sheet", "-o", path])

    def test_demo_unwritable_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "missing", "demo.html")
            self._assert_error(["demo", "-o", path])

    def test_missing_required_option(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(["distance"])
        self.assertEqual(ctx.exception.code, 2)

    def test_unknown_subcommand(self) -> None:
        err = io.StringIO()
        with redirect_stderr(err):
            with self.assertRaises(SystemExit) as ctx:
                main(["unknown"])
        self.assertEqual(ctx.exception.code, 2)


class TestParser(unittest.TestCase):
    def test_prog_name(self) -> None:
        self.assertEqual(build_parser().prog, "seismic")

    def test_help_contains_description(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("地震波", out.getvalue())


if __name__ == "__main__":
    unittest.main()
