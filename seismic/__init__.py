"""seismic：初中地理地震波与震级计算工具。"""

__version__ = "0.1.0"

from .core import (  # noqa: E402
    MAX_DISTANCE_KM,
    MAX_LAG_SECONDS,
    MAX_MAGNITUDE,
    MIN_MAGNITUDE,
    P_WAVE_SPEED,
    S_WAVE_SPEED,
    energy_ratio,
    epicenter_distance,
    normalize_wave,
    travel_time,
    wave_lag,
)
from .sheet import (  # noqa: E402
    Question,
    make_questions,
    render_demo,
    render_sheet,
    write_output,
)

__all__ = [
    "MAX_DISTANCE_KM",
    "MAX_LAG_SECONDS",
    "MAX_MAGNITUDE",
    "MIN_MAGNITUDE",
    "P_WAVE_SPEED",
    "S_WAVE_SPEED",
    "Question",
    "__version__",
    "energy_ratio",
    "epicenter_distance",
    "make_questions",
    "normalize_wave",
    "render_demo",
    "render_sheet",
    "travel_time",
    "wave_lag",
    "write_output",
]
