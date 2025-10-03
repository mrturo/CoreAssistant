# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from enum import Enum
from typing import Final, Optional

from src.model.core.exceptions import (DataSourceError, ItemStatusError,
                                       ItemTypeError)


class ItemType(str, Enum):
    TASK = "task"
    EVENT = "event"

    @classmethod
    def from_api(cls, raw: Optional[str]) -> Optional[ItemType]:
        if raw is None:
            return None
        try:
            return API_TO_TYPE[raw]
        except KeyError as exc:
            allowed = ", ".join(sorted(API_TO_TYPE.keys()))
            raise ItemTypeError(
                f"Unexpected type value: {raw!r}. Allowed: {allowed}."
            ) from exc


class ItemStatus(str, Enum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    CONFIRMED = "confirmed"
    NEEDS_ACTION = "needs_action"
    TENTATIVE = "tentative"

    @classmethod
    def from_api(cls, raw: Optional[str]) -> Optional[ItemStatus]:
        if raw is None:
            return None
        try:
            return API_TO_STATUS[raw]
        except KeyError as exc:
            allowed = ", ".join(sorted(API_TO_STATUS.keys()))
            raise ItemStatusError(
                f"Unexpected status value: {raw!r}. Allowed: {allowed}."
            ) from exc


class DataSource(str, Enum):
    GOOGLE_TASK = "google-task"
    GOOGLE_CALENDAR = "google-calendar"
    TODOIST = "todoist"

    @classmethod
    def from_api(cls, raw: Optional[str]) -> Optional[DataSource]:
        if raw is None:
            return None
        try:
            return API_TO_SOURCE[raw]
        except KeyError as exc:
            allowed = ", ".join(sorted(API_TO_SOURCE.keys()))
            raise DataSourceError(
                f"Unexpected data source value: {raw!r}. Allowed: {allowed}."
            ) from exc


class ItemGroup(Enum):
    DUED = (0, "DUED")
    ON_GOING = (1, "ON GOING")
    TODAY = (2, "TODAY")
    TOMORROW = (3, "TOMORROW")
    REST_OF_THIS_WEEK = (4, "REST OF THIS WEEK")
    THIS_FRIDAY = (5, "THIS FRIDAY")
    THIS_WEEKEND = (6, "THIS WEEKEND")
    THIS_SUNDAY = (7, "THIS SUNDAY")
    NEXT_WEEK = (8, "NEXT WEEK")
    REST_OF_THIS_MONTH = (9, "REST OF THIS MONTH")
    NEXT_MONTH = (10, "NEXT MONTH")
    FUTURE = (11, "FUTURE")

    def __init__(self, group_id: int, label: str) -> None:
        self._id = group_id
        self._label = label

    @property
    def id(self) -> int:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @classmethod
    def ordered(cls) -> list[ItemGroup]:
        return sorted(cls, key=lambda g: g.id)


API_TO_TYPE: Final[dict[str, ItemType]] = {
    "task": ItemType.TASK,
    "event": ItemType.EVENT,
}
API_TO_STATUS: Final[dict[str, ItemStatus]] = {
    "cancelled": ItemStatus.CANCELLED,
    "completed": ItemStatus.COMPLETED,
    "confirmed": ItemStatus.CONFIRMED,
    "needsAction": ItemStatus.NEEDS_ACTION,
    "tentative": ItemStatus.TENTATIVE,
}
API_TO_SOURCE: Final[dict[str, DataSource]] = {
    "google-task": DataSource.GOOGLE_TASK,
    "google-calendar": DataSource.GOOGLE_CALENDAR,
    "todoist": DataSource.TODOIST,
}
PlannedItemType = ItemType
PlannedItemStatus = ItemStatus
PlannedItemDataSource = DataSource
PlannedItemGroup = ItemGroup
