# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional

from src.model import ItemType


def is_true(value: Optional[bool]) -> bool:
    return value is True


def is_event(item_type: Optional[ItemType]) -> bool:
    if item_type is None:
        return False
    try:
        return item_type in (ItemType.EVENT, ItemType.EVENT.value)
    except AttributeError:
        return False
