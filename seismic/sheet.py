"""练习纸、演示页与题目生成。

HTML 全部用字符串拼接，文本一律经过 ``html.escape``，
不依赖第三方库，也不使用 xml.etree。
"""

import html
import math
import random
from typing import Dict, List, NamedTuple, Sequence, Tuple

from .core import (
    P_WAVE_SPEED,
    S_WAVE_SPEED,
    energy_ratio,
    epicenter_distance,
    travel_time,
    wave_lag,
)


class Question(NamedTuple):
    """一道练习题：题号、类型、题干、答案与解题过程。"""

    number: int
    kind: str
    prompt: str
    answer: str
    working: str


SHEET_CSS: str = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 18mm 14mm; background: #f4f6f9;
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  color: #1f2933; line-height: 1.7;
}
.sheet {
  max-width: 760px; margin: 0 auto; padding: 28px 32px;
  background: #ffffff; border: 1px solid #d8dee9; border-radius: 10px;
}
header { border-bottom: 2px solid #1f2933; padding-bottom: 10px; margin-bottom: 18px; }
h1 { margin: 0 0 6px; font-size: 24px; letter-spacing: 1px; }
.meta { margin: 0; font-size: 13px; color: #52606d; }
ol.questions { margin: 0; padding-left: 24px; }
ol.questions > li { margin-bottom: 22px; page-break-inside: avoid; }
.prompt { margin: 0 0 8px; font-size: 15px; }
.blank { height: 46px; border-bottom: 1px dashed #9aa5b1; }
.answer { margin: 4px 0; font-size: 14px; color: #0b7285; }
.working { margin: 0; font-size: 13px; color: #52606d; }
.tips { margin-top: 22px; padding-top: 10px; border-top: 1px solid #d8dee9;
  font-size: 12px; color: #616e7c; }
@media print {
  body { background: #ffffff; padding: 0; }
  .sheet { border: none; border-radius: 0; max-width: none; padding: 0; }
}
"""

DEMO_CSS: str = """
body {
  margin: 0; padding: 32px 18px; background: #f4f6f9;
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
  color: #1f2933; line-height: 1.7;
}
.wrap { max-width: 880px; margin: 0 auto; }
header { margin-bottom: 22px; }
h1 { margin: 0 0 5px; font-size: 26px; }
.sub { margin: 0; color: #52606d; font-size: 14px; }
figure { margin: 0 0 24px; padding: 14px; background: #ffffff;
  border: 1px solid #d8dee9; border-radius: 10px; }
figure svg { width: 100%; height: auto; display: block; }
figcaption { margin-top: 8px; font-size: 13px; color: #52606d; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
.card { padding: 16px 18px; background: #ffffff; border: 1px solid #d8dee9; border-radius: 10px; }
.card h2 { margin: 0 0 8px; font-size: 16px; color: #0b7285; }
.formula { margin: 6px 0; padding: 8px 10px; background: #f0f4f8; border-radius: 6px;
  font-family: "SFMono-Regular", Consolas, monospace; font-size: 14px; }
.note { margin: 6px 0 0; font-size: 13px; color: #616e7c; }
section.example { margin-top: 24px; padding: 18px 20px; background: #ffffff;
  border: 1px solid #d8dee9; border-radius: 10px; }
section.example h2 { margin: 0 0 10px; font-size: 18px; }
section.example ol { margin: 0; padding-left: 22px; font-size: 14px; }
section.example li { margin-bottom: 8px; }
"""


def to_int(value: object, name: str) -> int:
    """把外部输入转换为整数，拒绝布尔值、小数与非法文本。"""
    if isinstance(value, bool):
        raise ValueError("%s 不能是布尔值" % name)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or value != int(value):
            raise ValueError("%s 必须是整数" % name)
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s 不能为空" % name)
        try:
            return int(text)
        except ValueError:
            raise ValueError("%s 必须是整数，收到 %r" % (name, value)) from None
    raise ValueError("%s 必须是整数，收到 %r" % (name, value))


def _make_distance_question(number: int, rng: random.Random) -> Question:
    lag = round(rng.uniform(1.0, 40.0), 1)
    distance = epicenter_distance(lag)
    prompt = (
        "某地震台记录到 P 波与 S 波的到时差为 %.1f 秒，已知 P 波速度 %.1f 千米/秒、"
        "S 波速度 %.1f 千米/秒，求震中距（千米，保留 1 位小数）。"
        % (lag, P_WAVE_SPEED, S_WAVE_SPEED)
    )
    answer = "%.1f 千米" % distance
    working = (
        "d = 时差 × vP × vS ÷ (vP - vS) = %.1f × %.1f × %.1f ÷ %.1f ≈ %.1f 千米。"
        % (lag, P_WAVE_SPEED, S_WAVE_SPEED, P_WAVE_SPEED - S_WAVE_SPEED, distance)
    )
    return Question(number, "震中距", prompt, answer, working)


def _make_lag_question(number: int, rng: random.Random) -> Question:
    distance = round(rng.uniform(20.0, 500.0), 1)
    lag = wave_lag(distance)
    prompt = (
        "某次地震的震中距为 %.1f 千米，P 波速度 %.1f 千米/秒、S 波速度 %.1f 千米/秒，"
        "求地震台记录到的 P/S 波到时差（秒，保留 2 位小数）。"
        % (distance, P_WAVE_SPEED, S_WAVE_SPEED)
    )
    answer = "%.2f 秒" % lag
    working = (
        "Δt = d × (vP - vS) ÷ (vP × vS) = %.1f × %.1f ÷ %.1f ≈ %.2f 秒。"
        % (distance, P_WAVE_SPEED - S_WAVE_SPEED, P_WAVE_SPEED * S_WAVE_SPEED, lag)
    )
    return Question(number, "到时差", prompt, answer, working)


def _make_travel_question(number: int, rng: random.Random) -> Question:
    distance = round(rng.uniform(20.0, 500.0), 1)
    wave = rng.choice(["P", "S"])
    time = travel_time(distance, wave)
    speed = P_WAVE_SPEED if wave.upper() == "P" else S_WAVE_SPEED
    prompt = (
        "震源到某地震台的震中距为 %.1f 千米，求 %s 波从震源传到地震台的走时"
        "（秒，保留 2 位小数）。"
        % (distance, wave.upper())
    )
    answer = "%.2f 秒" % time
    working = "t = d ÷ v = %.1f ÷ %.1f ≈ %.2f 秒。" % (distance, speed, time)
    return Question(number, "走时", prompt, answer, working)


def _make_energy_question(number: int, rng: random.Random) -> Question:
    m1 = round(rng.uniform(1.0, 6.5), 1)
    m2 = round(min(9.9, m1 + rng.uniform(0.5, 2.5)), 1)
    ratio = energy_ratio(m1, m2)
    prompt = (
        "某地发生 %.1f 级地震，另一地发生 %.1f 级地震，后者的能量是前者的多少倍"
        "（保留 1 位小数）？" % (m1, m2)
    )
    answer = "%.1f 倍" % ratio
    working = (
        "E2 ÷ E1 = 10^(1.5 × (M2 - M1)) = 10^(1.5 × %.1f) ≈ %.1f 倍。"
        % (m2 - m1, ratio)
    )
    return Question(number, "能量倍数", prompt, answer, working)


def make_questions(count: int, seed: int) -> List[Question]:
    """按固定顺序生成练习纸题目。

    ``count`` 为 1..50 的整数，``seed`` 决定随机序列；
    相同种子得到完全相同的题目，便于批改与复现。
    """
    total = to_int(count, "题目数量")
    if total < 1 or total > 50:
        raise ValueError("题目数量必须在 1 到 50 之间")
    rng = random.Random(to_int(seed, "随机种子"))
    builders = (
        _make_distance_question,
        _make_lag_question,
        _make_travel_question,
        _make_energy_question,
    )
    questions: List[Question] = []
    for index in range(total):
        builder = builders[index % len(builders)]
        questions.append(builder(index + 1, rng))
    return questions


def _check_questions(questions: Sequence[Question]) -> List[Question]:
    """校验题目列表，空列表与错误类型直接报错。"""
    if questions is None:
        raise ValueError("题目列表不能为空")
    if isinstance(questions, (str, bytes)):
        raise ValueError("题目列表格式不正确")
    try:
        items = list(questions)
    except TypeError:
        raise ValueError("题目列表格式不正确") from None
    if not items:
        raise ValueError("题目列表不能为空")
    return items


def _document(title: str, css: str, body: str) -> str:
    """拼接完整的 HTML 文档。"""
    parts: List[str] = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>%s</title>" % html.escape(title),
        "<style>",
        css.strip(),
        "</style>",
        "</head>",
        "<body>",
        body,
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(parts)


def render_sheet(questions: Sequence[Question], answers: bool = False) -> str:
    """渲染 A4 练习纸；``answers`` 为 True 时附答案与解题过程。"""
    items = _check_questions(questions)
    body: List[str] = []
    body.append('<main class="sheet">')
    body.append("<header>")
    body.append("<h1>地震波与震级练习纸</h1>")
    body.append(
        '<p class="meta">共 %d 题　班级：__________　姓名：__________　日期：__________</p>'
        % len(items)
    )
    body.append("</header>")
    body.append('<ol class="questions">')
    for question in items:
        body.append("<li>")
        body.append('<p class="prompt">%s</p>' % html.escape(question.prompt))
        if answers:
            body.append('<p class="answer">答案：%s</p>' % html.escape(question.answer))
            body.append('<p class="working">过程：%s</p>' % html.escape(question.working))
        else:
            body.append('<div class="blank"></div>')
        body.append("</li>")
    body.append("</ol>")
    body.append(
        '<footer class="tips">提示：P 波速度 %.1f 千米/秒，S 波速度 %.1f 千米/秒；'
        "能量倍数按 10^(1.5×(M2-M1)) 计算。</footer>" % (P_WAVE_SPEED, S_WAVE_SPEED)
    )
    body.append("</main>")
    return _document("地震波与震级练习纸", SHEET_CSS, "\n".join(body))


def _semicircle(
    center_x: float,
    center_y: float,
    radius: float,
    stroke: str,
    width: float,
    dashed: bool,
) -> str:
    """画一个位于地面线之上的半圆弧，表示波前。"""
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    return (
        '<path d="M %.1f %.1f A %.1f %.1f 0 0 1 %.1f %.1f" fill="none" '
        'stroke="%s" stroke-width="%.1f"%s />'
        % (
            center_x - radius,
            center_y,
            radius,
            radius,
            center_x + radius,
            center_y,
            stroke,
            width,
            dash,
        )
    )


def _wave_svg() -> str:
    """手写 SVG：震源发出的 P 波与 S 波传播示意图。"""
    epicenter_x = 70.0
    ground_y = 200.0
    lines: List[str] = [
        '<svg viewBox="0 0 680 260" role="img" '
        'aria-label="P 波与 S 波从震源向地震台传播的示意图">',
        '<rect x="0" y="200" width="680" height="60" fill="#eef2f7" />',
        '<line x1="0" y1="200" x2="680" y2="200" stroke="#9aa5b1" stroke-width="2" />',
    ]
    for radius in (90.0, 150.0, 210.0, 270.0):
        lines.append(_semicircle(epicenter_x, ground_y, radius, "#d9480f", 2.0, False))
    for radius in (120.0, 190.0, 260.0):
        lines.append(_semicircle(epicenter_x, ground_y, radius, "#1971c2", 2.0, True))
    lines.extend(
        [
            '<line x1="%.1f" y1="%.1f" x2="600" y2="150" stroke="#52606d" '
            'stroke-width="1.5" stroke-dasharray="4 4" />' % (epicenter_x, ground_y),
            '<circle cx="%.1f" cy="%.1f" r="7" fill="#212529" />' % (epicenter_x, ground_y),
            '<text x="%.1f" y="232" font-size="13" fill="#212529" '
            'text-anchor="middle">震源</text>' % epicenter_x,
            '<polygon points="590,150 610,150 600,132" fill="#0b7285" />',
            '<text x="600" y="122" font-size="13" fill="#212529" '
            'text-anchor="middle">地震台</text>',
            '<text x="330" y="164" font-size="13" fill="#52606d" '
            'text-anchor="middle">震中距 d</text>',
            '<text x="220" y="44" font-size="13" fill="#d9480f">P 波 '
            '%.1f 千米/秒（实线）</text>' % P_WAVE_SPEED,
            '<text x="220" y="66" font-size="13" fill="#1971c2">S 波 '
            '%.1f 千米/秒（虚线）</text>' % S_WAVE_SPEED,
            "</svg>",
        ]
    )
    return "\n".join(lines)


def render_demo() -> str:
    """渲染演示页：P/S 波传播示意图、公式卡片与例题。"""
    example_lag = 5.0
    example_distance = epicenter_distance(example_lag)
    example_ratio = energy_ratio(5.0, 7.0)
    body: List[str] = []
    body.append('<div class="wrap">')
    body.append("<header>")
    body.append("<h1>地震波与震级</h1>")
    body.append(
        '<p class="sub">P 波跑得快、先到达；S 波跑得慢、后到达。'
        "两者的到时差可以用来估算震中距。</p>"
    )
    body.append("</header>")
    body.append("<figure>")
    body.append(_wave_svg())
    body.append(
        "<figcaption>同一震源发出的 P 波（实线）与 S 波（虚线），"
        "地震台先记录到 P 波，再过一段时间记录到 S 波。</figcaption>"
    )
    body.append("</figure>")
    body.append('<div class="cards">')

    cards: List[Tuple[str, str, str]] = [
        (
            "由到时差求震中距",
            "d = Δt × vP × vS ÷ (vP - vS)",
            "vP = %.1f 千米/秒，vS = %.1f 千米/秒。" % (P_WAVE_SPEED, S_WAVE_SPEED),
        ),
        (
            "由震中距求到时差",
            "Δt = d × (vP - vS) ÷ (vP × vS)",
            "到时差越大，震中距越远。",
        ),
        (
            "单波走时",
            "t = d ÷ v",
            "P 波走时短，S 波走时长。",
        ),
        (
            "震级与能量",
            "E2 ÷ E1 = 10^(1.5 × (M2 - M1))",
            "震级每增加 1 级，能量约增大 31.6 倍。",
        ),
    ]
    for title, formula, note in cards:
        body.append('<section class="card">')
        body.append("<h2>%s</h2>" % html.escape(title))
        body.append('<p class="formula">%s</p>' % html.escape(formula))
        body.append('<p class="note">%s</p>' % html.escape(note))
        body.append("</section>")
    body.append("</div>")

    body.append('<section class="example">')
    body.append("<h2>例题</h2>")
    body.append("<ol>")
    body.append(
        "<li>某台站记录到 P 波与 S 波的到时差为 %.1f 秒，"
        "求震中距：d = %.1f × %.1f × %.1f ÷ %.1f ≈ %.1f 千米。</li>"
        % (
            example_lag,
            example_lag,
            P_WAVE_SPEED,
            S_WAVE_SPEED,
            P_WAVE_SPEED - S_WAVE_SPEED,
            example_distance,
        )
    )
    body.append(
        "<li>5.0 级地震与 7.0 级地震的能量倍数："
        "10^(1.5 × 2.0) = %.1f 倍。</li>" % example_ratio
    )
    body.append(
        "<li>震中距 %d 千米处，P 波走时约为 %.1f 秒，S 波走时约为 %.1f 秒。</li>"
        % (100, travel_time(100.0, "p"), travel_time(100.0, "s"))
    )
    body.append("</ol>")
    body.append("</section>")
    body.append("</div>")
    return _document("地震波与震级演示", DEMO_CSS, "\n".join(body))


def write_output(path: str, content: str) -> None:
    """把文本写入文件（UTF-8）；路径非法或写入失败时抛出中文 ``ValueError``。"""
    if not isinstance(path, str):
        raise ValueError("输出路径必须是字符串")
    target = path.strip()
    if not target:
        raise ValueError("输出路径不能为空")
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError("写入文件失败：%s" % exc) from None


__all__ = [
    "Question",
    "make_questions",
    "render_demo",
    "render_sheet",
    "to_int",
    "write_output",
]
