# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class ItemNode(Protocol):
    id: str
    parent: Optional[str]
    title: str
    position: Optional[str]
    subitems: list[ItemNode]

    def add_subitem(self, subitem: ItemNode) -> None: ...
    def is_root(self) -> bool: ...
