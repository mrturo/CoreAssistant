# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from enum import Enum


class PlannedItemGroup(Enum):

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
    def ordered(cls) -> list[PlannedItemGroup]:
        return sorted(cls, key=lambda g: g.id)

    @classmethod
    def from_label(cls, label: str) -> PlannedItemGroup:
        normalized = label.strip().casefold()
        for group in cls:
            if group.label.casefold() == normalized:
                return group
        raise ValueError(f"Unknown group label: {label!r}")
