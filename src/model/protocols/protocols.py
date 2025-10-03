# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Iterable, Optional, Protocol, Sequence, runtime_checkable

from src.model import ItemStatus, PlannedItemList


@runtime_checkable
class ItemLike(Protocol):
    title: str
    status: Optional[ItemStatus]
    start_raw: Optional[str]
    end_raw: Optional[str]
    subitems: Sequence[ItemLike]
    planned_item_list: Optional[PlannedItemList]

    def is_all_day(self) -> bool: ...
    def is_ongoing(self) -> bool: ...
    def calendar_days(self) -> int: ...
    def duration_str(self) -> Optional[str]: ...
    def time_until_start_str(self) -> str: ...
    def time_until_end_str(self) -> str: ...


@runtime_checkable
class ItemRenderer(Protocol):
    def render(self, items: Iterable[ItemLike]) -> str:
        raise NotImplementedError


@runtime_checkable
class ItemLineFormatter(Protocol):
    def format_line(self, item: ItemLike, level: int, indent_size: int) -> str:
        raise NotImplementedError
