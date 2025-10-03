# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.common.data.data_operations import (_apply_auto_complete_to_tasks,
                                             _fetch_from_lists)
from src.model import PlannedItem, PlannedItemList
from src.sources.gcp import gcp


class DataFetcher:
    @staticmethod
    def get_pending_tasks(task_lists: List[PlannedItemList]) -> List[PlannedItem]:
        return _fetch_from_lists(
            lists=task_lists,
            list_type_name="task lists",
            fetch_func=gcp.get_pending_tasks,
        )

    @staticmethod
    def get_pending_tasks_with_auto_complete(
        task_lists: List[PlannedItemList],
    ) -> List[PlannedItem]:
        tasks = _fetch_from_lists(
            lists=task_lists,
            list_type_name="task lists",
            fetch_func=gcp.get_pending_tasks,
        )

        return _apply_auto_complete_to_tasks(tasks, task_lists, gcp.get_pending_tasks)

    @staticmethod
    def get_upcoming_events(calendars_list: List[PlannedItemList]) -> List[PlannedItem]:
        return _fetch_from_lists(
            lists=calendars_list,
            list_type_name="calendars",
            fetch_func=gcp.get_upcoming_events,
        )
