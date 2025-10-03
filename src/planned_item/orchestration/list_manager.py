# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.common.data.data_operations import get_calendars_list, get_task_lists
from src.model import PlannedItemList


class ListManager:
    @staticmethod
    def get_task_lists() -> List[PlannedItemList]:
        return get_task_lists()

    @staticmethod
    def get_calendars_list() -> List[PlannedItemList]:
        return get_calendars_list()
