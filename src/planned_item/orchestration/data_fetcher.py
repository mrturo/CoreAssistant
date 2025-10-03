# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.common.data.data_operations import (_apply_auto_complete_to_tasks,
                                             _fetch_from_lists,
                                             get_all_pending_tasks,
                                             get_all_pending_tasks_with_auto_complete,
                                             get_todoist_pending_tasks,
                                             get_todoist_pending_tasks_with_auto_complete)
from src.model import PlannedItem, PlannedItemList
from src.sources.gcp import gcp
from src.sources.todoist import todoist


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

        return _apply_auto_complete_to_tasks(tasks, task_lists, gcp.get_pending_tasks, gcp.auto_complete_parent_tasks)

    @staticmethod
    def get_upcoming_events(calendars_list: List[PlannedItemList]) -> List[PlannedItem]:
        return _fetch_from_lists(
            lists=calendars_list,
            list_type_name="calendars",
            fetch_func=gcp.get_upcoming_events,
        )

    @staticmethod
    def get_todoist_pending_tasks(project_lists: List[PlannedItemList]) -> List[PlannedItem]:
        return _fetch_from_lists(
            lists=project_lists,
            list_type_name="Todoist projects",
            fetch_func=todoist.get_pending_tasks,
        )

    @staticmethod
    def get_todoist_pending_tasks_with_auto_complete(
        project_lists: List[PlannedItemList],
    ) -> List[PlannedItem]:
        tasks = _fetch_from_lists(
            lists=project_lists,
            list_type_name="Todoist projects",
            fetch_func=todoist.get_pending_tasks,
        )

        return _apply_auto_complete_to_tasks(
            tasks, project_lists, todoist.get_pending_tasks, todoist.auto_complete_parent_tasks
        )

    @staticmethod
    def get_all_pending_tasks() -> List[PlannedItem]:
        return get_all_pending_tasks()

    @staticmethod
    def get_all_pending_tasks_with_auto_complete() -> List[PlannedItem]:
        return get_all_pending_tasks_with_auto_complete()
