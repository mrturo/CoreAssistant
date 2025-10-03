# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class TaskQueryConfig:
    max_items: int = 200
    include_undated: bool = True
    show_tz_shadow: bool = False
    filter_local_date: Optional[date] = None
