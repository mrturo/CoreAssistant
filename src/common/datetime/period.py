# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

from src.common.data.parameters import ParameterLoader

params = ParameterLoader()
today: date = params.get("TODAY")
DEFAULT_DURATION: int = 60


def _validate_types(
    start: Optional[date], end: Optional[date], duration: Optional[int]
) -> None:
    if start is not None and not isinstance(start, date):
        raise TypeError("'start' must be a datetime.date instance or None")
    if end is not None and not isinstance(end, date):
        raise TypeError("'end' must be a datetime.date instance or None")
    if duration is not None and not isinstance(duration, int):
        raise TypeError("'duration' must be an int or None")


def _min_duration(inclusive: bool) -> int:
    return 1 if inclusive else 0


def _span_days(duration: int, inclusive: bool) -> int:
    return duration - 1 if inclusive else duration


def _derive_bounds(
    ref_today: date,
    start: Optional[date],
    end: Optional[date],
    *,
    duration: int,
    inclusive: bool,
) -> Tuple[date, date]:
    provided = int(start is not None) + int(end is not None)
    if provided == 0:
        half = duration // 2
        start_calc = ref_today - timedelta(days=duration - half)
        end_calc = ref_today + timedelta(days=half)
        return start_calc, end_calc
    if provided == 2:
        if end < start:  # type: ignore[operator]
            raise ValueError("'end' cannot be earlier than 'start'")
        return start, end  # type: ignore[return-value]
    if start is not None:
        end_calc = start + timedelta(days=_span_days(duration, inclusive))
        return start, end_calc
    if end is None:
        raise ValueError("Internal error: 'end' expected to be non-None here.")
    start_calc = end - timedelta(days=_span_days(duration, inclusive))
    return start_calc, end


class Period:
    def __init__(
        self,
        start: Optional[date] = None,
        end: Optional[date] = None,
        duration: Optional[int] = None,
        *,
        inclusive: bool = False,
    ) -> None:
        _validate_types(start, end, duration)
        user_supplied_duration = duration is not None
        duration = duration if duration is not None else DEFAULT_DURATION
        if duration < _min_duration(inclusive):
            raise ValueError(
                f"'duration' must be >= {_min_duration(inclusive)} with inclusive={inclusive}"
            )
        start_calc, end_calc = _derive_bounds(
            today,
            start,
            end,
            duration=duration,
            inclusive=inclusive,
        )
        if end_calc < start_calc:
            raise ValueError("Invariant violated: end < start")
        self.start: date = start_calc
        self.end: date = end_calc
        self._inclusive: bool = inclusive
        computed = (self.end - self.start).days + (1 if inclusive else 0)
        self.duration: int = duration if user_supplied_duration else computed

    def __repr__(self) -> str:
        return (
            f"Period(start={self.start!r}, end={self.end!r}, "
            f"duration={self.duration}, inclusive={self._inclusive})"
        )
