# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from src.model.list.list_metadata import ListMetadata

Kind = Literal["calendar", "tasklist"]


@dataclass
class ItemList:
    kind: Kind
    id: str
    name: Optional[str] = None
    metadata: Optional[ListMetadata] = None


PlannedItemList = ItemList
