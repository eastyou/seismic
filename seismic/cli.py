"""命令行入口。"""

import argparse
import sys
from typing import List, Optional, Sequence

from . import __version__
from .core import (
    energy_ratio,
    epicenter_distance,
    travel_time,
    wave_lag,
)
from .sheet import make_questions, render_demo, render_sheet, write_output


def _ensure_utf8_console() -> None:
    """把标准输出与标准错误尽量切换为 UTF-8，失败时保持原状。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def build_parser() -> argparse.ArgumentParser:
    """构建命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="seismic",
        description="初中地理：地震波与震级计算工具。",
    )
    parser.add_argument("--version", action="version", version="seismic " + __version__)
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="子命令")

    distance = subparsers.add_parser("distance", help="由 P/S 波到时差求震中距")
    distance.add_argument("--lag", required=True, type=str, metavar="秒", help="P/S 波到时差（秒）")

    lag = subparsers.add_parser("lag", help="由震中距求 P/S 波到时差")
    lag.add_argument("--distance", required=True, type=str, metavar="千米", help="震中距（千米）")

    travel = subparsers.add_parser("travel", help="求某类地震波的走时")
    travel.add_argument("--distance", required=True, type=str, metavar="千米", help="震中距（千米）")
    travel.add_argument("--wave", default="p", type=str, metavar="p/s", help="波型，p 或 s，默认 p")

    energy = subparsers.add_parser("energy", help="求两个震级之间的能量倍数")
    energy.add_argument("--m1", required=True, type=str, metavar="震级", help="起始震级 M1")
    energy.add_argument("--m2", required=True, type=str, metavar="震级", help="目标震级 M2")

    sheet = subparsers.add_parser("sheet", help="生成 A4 练习纸")
    sheet.add_argument("--count", default="8", type=str, metavar="题数", help="题目数量，1 到 50，默认 8")
    sheet.add_argument("--seed", default="1", type=str, metavar="整数", help="随机种子，默认 1")
    sheet.add_argument("-o", "--output", required=True, type=str, metavar="路径", help="输出 HTML 文件")
    sheet.add_argument("--answers", action="store_true", help="在练习纸上附答案与解题过程")

    demo = subparsers.add_parser("demo", help="生成演示页")
    demo.add_argument("-o", "--output", required=True, type=str, metavar="路径", help="输出 HTML 文件")

    return parser


def _run(args: argparse.Namespace) -> int:
    """根据子命令执行计算或生成页面。"""
    command = args.command
    if command == "distance":
        lag = args.lag
        value = epicenter_distance(lag)
        print("震中距：%.1f 千米" % value)
        print("依据：d = 时差 × vP × vS ÷ (vP - vS)，时差 %s 秒" % lag.strip())
        return 0
    if command == "lag":
        distance = args.distance
        value = wave_lag(distance)
        print("P/S 波到时差：%.2f 秒" % value)
        print("依据：Δt = d × (vP - vS) ÷ (vP × vS)，震中距 %s 千米" % distance.strip())
        return 0
    if command == "travel":
        distance = args.distance
        wave = args.wave
        value = travel_time(distance, wave)
        print("%s 波走时：%.2f 秒" % (wave.strip().upper(), value))
        print("依据：t = d ÷ v，震中距 %s 千米" % distance.strip())
        return 0
    if command == "energy":
        m1 = args.m1
        m2 = args.m2
        value = energy_ratio(m1, m2)
        print("能量倍数：%.1f 倍" % value)
        print(
            "依据：E2 ÷ E1 = 10^(1.5 × (M2 - M1))，M1 = %s，M2 = %s"
            % (m1.strip(), m2.strip())
        )
        return 0
    if command == "sheet":
        questions = make_questions(args.count, args.seed)
        content = render_sheet(questions, args.answers)
        write_output(args.output, content)
        print("已生成练习纸：%s" % args.output)
        print("题目数：%d，答案：%s" % (len(questions), "含" if args.answers else "不含"))
        return 0
    if command == "demo":
        content = render_demo()
        write_output(args.output, content)
        print("已生成演示页：%s" % args.output)
        return 0
    raise ValueError("未知子命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，返回退出码：成功 0，输入或写入失败 2。"""
    _ensure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2


__all__: List[str] = ["build_parser", "main"]
