# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from enum import Enum
from typing import Final, Optional


class PlannedItemTypeError(ValueError): ...


class PlannedItemType(str, Enum):
    TASK = "task"
    EVENT = "event"

    @classmethod
    def from_api(cls, raw: Optional[str]) -> Optional[PlannedItemType]:
        if raw is None:
            return None
        try:
            return API_TO_TYPE[raw]
        except KeyError as exc:
            allowed = ", ".join(sorted(API_TO_TYPE.keys()))
            raise PlannedItemTypeError(
                f"Unexpected type value: {raw!r}. Allowed: {allowed}."
            ) from exc


API_TO_TYPE: Final[dict[str, PlannedItemType]] = {
    "task": PlannedItemType.TASK,
    "event": PlannedItemType.EVENT,
}
