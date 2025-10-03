# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.model import ItemType, PlannedItemList
from src.model.core.enums import DataSource


@dataclass(frozen=True)
class DateFlags:
    is_today_or_tomorrow: bool = False
    is_before_today: bool = False
    is_today: bool = False
    is_tomorrow: bool = False


@dataclass(frozen=True)
class StateFlags:
    is_on_going: bool = False
    is_ongoing: bool = False


@dataclass(frozen=True)
class TimeHints:
    duration_str: Optional[str] = None
    time_until_start_str: Optional[str] = None
    time_until_end_str: Optional[str] = None


@dataclass(frozen=True)
class FormattingFlags:
    date: DateFlags
    state: StateFlags
    time: TimeHints


@dataclass(frozen=True)
class HumanizeContext:
    item_type: Optional[ItemType]
    is_all_day: bool
    calendar_days: int
    is_today_or_tomorrow: bool
    is_on_going: bool
    start_raw: Optional[str]
    end_raw: Optional[str]


@dataclass(frozen=True)
class ItemMeta:
    item_type: Optional[ItemType]
    is_all_day: bool
    calendar_days: int


@dataclass(frozen=True)
class Timing:
    start: Optional[str]
    end: Optional[str]


@dataclass(frozen=True)
class DetailsContext:
    meta: ItemMeta
    timing: Timing
    location: Optional[str]
    flags: FormattingFlags
    planned_item_list: Optional[PlannedItemList] = None
    data_source: Optional[DataSource] = None


@dataclass(frozen=True)
class StartContext:
    is_all_day: Optional[bool] = None
    calendar_days: Optional[int] = None
    is_today_or_tomorrow: Optional[bool] = None
    is_on_going: Optional[bool] = None
    item_type: Optional[ItemType] = None


@dataclass(frozen=True)
class EndContext:
    is_all_day: Optional[bool] = None
    calendar_days: Optional[int] = None
