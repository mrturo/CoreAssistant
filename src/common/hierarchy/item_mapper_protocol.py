# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Mapping, Protocol

from src.common.hierarchy.item_node import ItemNode


class ItemMapperProtocol(Protocol):
    def to_entity(self, raw: Mapping[str, object]) -> ItemNode: ...
