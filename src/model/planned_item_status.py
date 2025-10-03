# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from enum import Enum
from typing import Final, Optional


class PlannedItemStatusError(ValueError): ...


class PlannedItemStatus(str, Enum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    CONFIRMED = "confirmed"
    NEEDS_ACTION = "needs_action"
    TENTATIVE = "tentative"

    @classmethod
    def from_api(cls, raw: Optional[str]) -> Optional[PlannedItemStatus]:
        if raw is None:
            return None
        try:
            return API_TO_STATUS[raw]
        except KeyError as exc:
            allowed = ", ".join(sorted(API_TO_STATUS.keys()))
            raise PlannedItemStatusError(
                f"Unexpected status value: {raw!r}. Allowed: {allowed}."
            ) from exc


API_TO_STATUS: Final[dict[str, PlannedItemStatus]] = {
    "cancelled": PlannedItemStatus.CANCELLED,
    "completed": PlannedItemStatus.COMPLETED,
    "confirmed": PlannedItemStatus.CONFIRMED,
    "needsAction": PlannedItemStatus.NEEDS_ACTION,
    "tentative": PlannedItemStatus.TENTATIVE,
}
