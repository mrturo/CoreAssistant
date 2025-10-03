# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import datetime
from typing import Any, Collection

from src.common.datetime.period import Period
from src.model import PlannedItemGroup


def is_valid_group(group: Any, period: Any, group_items: Any) -> bool:
    if not group or not isinstance(group, PlannedItemGroup):
        return False
    if (
        not period
        or not isinstance(period, Period)
        or period.start is None
        or not isinstance(period.start, datetime.date)
    ):
        return False
    if (
        not group_items
        or not isinstance(group_items, Collection)
        or len(group_items) == 0
    ):
        return False
    return True
