# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Kind = Literal["calendar", "tasklist"]


@dataclass
class PlannedItemListMetadata:
    access_role: Optional[str] = None
    time_zone: Optional[str] = None
    updated: Optional[str] = None
    self_link: Optional[str] = None
    primary: bool = False


@dataclass
class PlannedItemList:
    kind: Kind
    id: str
    name: Optional[str] = None
    metadata: Optional[PlannedItemListMetadata] = None
