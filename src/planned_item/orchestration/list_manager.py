# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.common.data.data_operations import (get_calendars_list, get_task_lists, 
                                                      get_todoist_projects_list)
from src.model import PlannedItemList


class ListManager:
    @staticmethod
    def get_task_lists() -> List[PlannedItemList]:
        return get_task_lists()

    @staticmethod
    def get_calendars_list() -> List[PlannedItemList]:
        return get_calendars_list()

    @staticmethod
    def get_todoist_projects() -> List[PlannedItemList]:
        return get_todoist_projects_list()

    @staticmethod
    def get_all_task_sources() -> List[PlannedItemList]:
        google_lists = get_task_lists()
        todoist_projects = get_todoist_projects_list()
        return google_lists + todoist_projects
