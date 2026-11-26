"""地震波与震级的核心计算。

本模块只使用标准库。所有对外函数都会校验参数，
非法输入统一抛出中文 ``ValueError``，方便命令行层转成退出码 2。
"""

import math
from typing import Dict, Tuple

# P 波与 S 波在均匀地壳中的平均速度，单位：千米/秒
P_WAVE_SPEED: float = 6.0
S_WAVE_SPEED: float = 3.5

# 输入范围
MAX_LAG_SECONDS: float = 3600.0
MAX_DISTANCE_KM: float = 20000.0
MIN_MAGNITUDE: float = 0.0
MAX_MAGNITUDE: float = 9.9

# 计算结果的安全上限
MAX_RESULT: float = 1e15

VALID_WAVES: Tuple[str, ...] = ("p", "s")
WAVE_SPEEDS: Dict[str, float] = {"p": P_WAVE_SPEED, "s": S_WAVE_SPEED}


def to_float(value: object, name: str) -> float:
    """把外部输入转换为浮点数。

    拒绝布尔值（bool 不算数值）、空字符串、非数字文本、
    NaN 与正负无穷大；转换失败时抛出中文 ``ValueError``。
    """
    if isinstance(value, bool):
        raise ValueError("%s 不能是布尔值" % name)
    if isinstance(value, (int, float)):
        try:
            result = float(value)
        except OverflowError:
            raise ValueError("%s 数值过大，无法处理" % name) from None
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s 不能为空" % name)
        try:
            result = float(text)
        except ValueError:
            raise ValueError("%s 必须是数字，收到 %r" % (name, value)) from None
    else:
        raise ValueError("%s 必须是数字，收到 %r" % (name, value))
    if not math.isfinite(result):
        raise ValueError("%s 不能是 NaN 或无穷大" % name)
    return result


def check_lag(lag_seconds: object) -> float:
    """校验 P/S 波到时差（秒）：必须大于 0 且小于 3600。"""
    lag = to_float(lag_seconds, "到时差")
    if lag <= 0.0:
        raise ValueError("到时差必须大于 0 秒")
    if lag >= MAX_LAG_SECONDS:
        raise ValueError("到时差必须小于 3600 秒")
    return lag


def check_distance(distance_km: object) -> float:
    """校验震中距（千米）：必须大于 0 且小于 20000。"""
    distance = to_float(distance_km, "震中距")
    if distance <= 0.0:
        raise ValueError("震中距必须大于 0 千米")
    if distance >= MAX_DISTANCE_KM:
        raise ValueError("震中距必须小于 20000 千米")
    return distance


def check_magnitude(value: object, name: str) -> float:
    """校验震级：必须在 0 到 9.9 之间（含端点）。"""
    magnitude = to_float(value, name)
    if magnitude < MIN_MAGNITUDE or magnitude > MAX_MAGNITUDE:
        raise ValueError("%s 必须在 0 到 9.9 之间" % name)
    return magnitude


def normalize_wave(wave: object) -> str:
    """把波型归一成小写 ``p`` 或 ``s``，其余输入一律拒绝。"""
    if not isinstance(wave, str):
        raise ValueError("波型必须是字符串 p 或 s")
    text = wave.strip().lower()
    if text not in VALID_WAVES:
        raise ValueError("波型只能是 p 或 s，收到 %r" % wave)
    return text


def _check_result(value: float, name: str) -> float:
    """确保结果有限且不超过安全上限。"""
    if not math.isfinite(value):
        raise ValueError("%s 计算结果无效" % name)
    if abs(value) >= MAX_RESULT:
        raise ValueError("%s 超出可计算范围" % name)
    return value


def epicenter_distance(lag_seconds: float) -> float:
    """由 P/S 波到时差求震中距（千米）。

    ``d = Δt × vP × vS / (vP - vS)``
    """
    lag = check_lag(lag_seconds)
    distance = lag * P_WAVE_SPEED * S_WAVE_SPEED / (P_WAVE_SPEED - S_WAVE_SPEED)
    return _check_result(distance, "震中距")


def wave_lag(distance_km: float) -> float:
    """由震中距求 P/S 波到时差（秒）。

    ``Δt = d × (vP - vS) / (vP × vS)``
    """
    distance = check_distance(distance_km)
    lag = distance * (P_WAVE_SPEED - S_WAVE_SPEED) / (P_WAVE_SPEED * S_WAVE_SPEED)
    return _check_result(lag, "到时差")


def travel_time(distance_km: float, wave: str) -> float:
    """某类地震波从震源到给定距离的走时（秒）。

    ``t = d / v``，``wave`` 只接受 p 或 s（忽略大小写与首尾空格）。
    """
    distance = check_distance(distance_km)
    wave_key = normalize_wave(wave)
    return _check_result(distance / WAVE_SPEEDS[wave_key], "走时")


def energy_ratio(m1: float, m2: float) -> float:
    """两个震级之间的能量倍数，``ratio = 10^(1.5 × (M2 - M1))``。

    要求 0 ≤ M1 ≤ M2 ≤ 9.9。
    """
    first = check_magnitude(m1, "起始震级 M1")
    second = check_magnitude(m2, "目标震级 M2")
    if second < first:
        raise ValueError("目标震级 M2 不能小于起始震级 M1")
    return _check_result(10.0 ** (1.5 * (second - first)), "能量倍数")
