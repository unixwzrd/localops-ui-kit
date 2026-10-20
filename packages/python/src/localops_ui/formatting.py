"""Backend-neutral display formatting."""

from __future__ import annotations

import math


def format_duration(seconds: float | None) -> str:
    if seconds is None or not math.isfinite(seconds) or seconds < 0:
        return "—"
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60:
        return f"{seconds:.1f} s" if seconds < 10 else f"{seconds:.0f} s"
    minutes, remainder = divmod(round(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {remainder:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def format_number(value: float | int | None, *, maximum_fraction_digits: int = 2) -> str:
    if value is None or not math.isfinite(value):
        return "—"
    return f"{value:,.{maximum_fraction_digits}f}".rstrip("0").rstrip(".")
