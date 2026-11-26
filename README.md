# seismic

[![CI](https://github.com/eastyou/seismic/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/seismic/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

一个面向初中地理课堂的地震波与震级计算工具，同时可以生成 A4 练习纸与演示页。

固定使用 P 波速度 6.0 千米/秒、S 波速度 3.5 千米/秒，围绕「到时差、震中距、走时、能量倍数」四类问题做计算、出题与排版；全部使用 Python 标准库，零第三方依赖。

## 特性

- 由 P/S 波到时差反推震中距，也可由震中距正算到时差，两个方向互相校验。
- 支持单独计算 P 波或 S 波从震源到指定距离的走时。
- 按 `10^(1.5×(M2-M1))` 计算震级差对应的能量倍数。
- 一条命令生成 A4 打印版练习纸，`--answers` 可附加答案与解题过程。
- `demo` 子命令手写 SVG 绘制 P/S 波传播示意图，并附公式卡片与例题。
- 相同 `--seed` 生成的练习纸完全一致，方便批改与重复印发。
- 所有外部输入都会校验：布尔值、空值、非数字、NaN、无穷大与越界值都会被拒绝。
- 全部函数带类型注解，兼容 Python 3.9 及以上版本。

## 安装

```bash
pip install .
```

安装后可直接使用 `seismic` 命令，也可以 `python -m seismic` 运行。

## 使用

```bash
$ seismic --help
usage: seismic [-h] [--version] 子命令 ...

初中地理：地震波与震级计算工具。

positional arguments:
  子命令
    distance  由 P/S 波到时差求震中距
    lag       由震中距求 P/S 波到时差
    travel    求某类地震波的走时
    energy    求两个震级之间的能量倍数
    sheet     生成 A4 练习纸
    demo      生成演示页

options:
  -h, --help  show this help message and exit
  --version   show program's version number and exit
```

```bash
$ seismic distance --lag 5
震中距：42.0 千米
依据：d = 时差 × vP × vS ÷ (vP - vS)，时差 5 秒

$ seismic lag --distance 70
P/S 波到时差：8.33 秒
依据：Δt = d × (vP - vS) ÷ (vP × vS)，震中距 70 千米

$ seismic travel --distance 100 --wave p
P 波走时：16.67 秒
依据：t = d ÷ v，震中距 100 千米

$ seismic travel --distance 100 --wave s
S 波走时：28.57 秒
依据：t = d ÷ v，震中距 100 千米

$ seismic energy --m1 5 --m2 7
能量倍数：1000.0 倍
依据：E2 ÷ E1 = 10^(1.5 × (M2 - M1))，M1 = 5，M2 = 7

$ seismic sheet --count 8 --seed 1 -o sheet.html
已生成练习纸：sheet.html
题目数：8，答案：不含

$ seismic sheet --count 4 --seed 2 --answers -o answers.html
已生成练习纸：answers.html
题目数：4，答案：含

$ seismic demo -o demo.html
已生成演示页：demo.html
```

输入非法时，错误信息写入标准错误并返回退出码 2：

```bash
$ seismic distance --lag abc
错误：到时差 必须是数字，收到 'abc'
$ echo $?
2
```

### 参数

| 子命令 | 参数 | 说明 | 取值范围 |
| --- | --- | --- | --- |
| `distance` | `--lag` | P/S 波到时差（秒） | 大于 0 且小于 3600 |
| `lag` | `--distance` | 震中距（千米） | 大于 0 且小于 20000 |
| `travel` | `--distance` | 震中距（千米） | 大于 0 且小于 20000 |
| `travel` | `--wave` | 波型，p 或 s（不区分大小写） | 默认 `p` |
| `energy` | `--m1` | 起始震级 M1 | 0 到 9.9 |
| `energy` | `--m2` | 目标震级 M2，且不小于 M1 | 0 到 9.9 |
| `sheet` | `--count` | 练习题数量 | 1 到 50，默认 8 |
| `sheet` | `--seed` | 随机种子 | 任意整数，默认 1 |
| `sheet` | `-o, --output` | 输出 HTML 文件路径 | 必填 |
| `sheet` | `--answers` | 是否附答案与解题过程 | 开关项 |
| `demo` | `-o, --output` | 输出 HTML 文件路径 | 必填 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 计算成功或文件生成成功 |
| 2 | 参数缺失、输入非法、越界或写入文件失败 |

## 作为库使用

```python
from seismic import (
    energy_ratio,
    epicenter_distance,
    make_questions,
    render_sheet,
    travel_time,
    wave_lag,
)

print(round(epicenter_distance(5), 1))        # 42.0
print(round(wave_lag(70), 2))                 # 8.33
print(round(travel_time(100, "p"), 2))        # 16.67
print(round(energy_ratio(5, 7), 1))           # 1000.0

questions = make_questions(count=8, seed=1)
html_text = render_sheet(questions, answers=True)
print(len(questions))                         # 8
```

## 开发与测试

```bash
python -m unittest discover -s tests -v
```

共 119 个测试用例，覆盖计算正常值、边界值（时差为 0、距离达到上限、M2 小于 M1、非法波型）、非法输入的错误码与错误信息、HTML 可被 `html.parser` 解析、种子可复现以及每个子命令。

## License

[MIT](LICENSE) © 2026 eastyou
