# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass

from src.common.hierarchy.item_node import ItemNode


def _default_sort_key(item: ItemNode) -> tuple[str, str]:
    pos = item.position if item.position is not None else "\uffff"
    ttl = item.title if item.title is not None else ""
    return pos, ttl


@dataclass(frozen=True)
class DefaultItemSorter:
    def sort(self, items: list[ItemNode]) -> None:
        items.sort(key=_default_sort_key)
