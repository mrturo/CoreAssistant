# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Final
from zoneinfo import ZoneInfo

from src.common.data.parameters import ParameterLoader

_PARAMS = ParameterLoader()
DEFAULT_TZINFO: Final[ZoneInfo] = _PARAMS.get("TZINFO")
DEFAULT_TODAY: Final[date] = _PARAMS.get("TODAY")
DEFAULT_NOW: Final[datetime] = _PARAMS.get("NOW")


@dataclass(frozen=True)
class EnvClock:
    tzinfo: ZoneInfo = DEFAULT_TZINFO
    today: date = DEFAULT_TODAY
    now: datetime = DEFAULT_NOW
