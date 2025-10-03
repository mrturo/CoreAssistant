# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Dict, List, Optional

from src.model import PlannedItem, PlannedItemList
from src.sources.todoist.auth.settings import TodoistAuthSettings
from src.sources.todoist.todoist_planned_source import TodoistPlannedSource

DEFAULT_PROJECT_ID = "inbox"


def _default_source() -> TodoistPlannedSource:
    return TodoistPlannedSource()


def get_pending_tasks(
    planned_list: Optional[PlannedItemList] = None,
    max_items: int = 200,
) -> List[PlannedItem]:
    return _default_source().get_pending_tasks(
        planned_list=planned_list, max_items=max_items
    )


def get_projects_list(max_items: int = 100) -> List[Dict[str, Optional[str]]]:
    return _default_source().get_projects_list(max_items=max_items)


def get_labels_list(max_items: int = 100) -> List[Dict[str, Optional[str]]]:
    return _default_source().get_labels_list(max_items=max_items)


def get_tasks_by_filter(
    filter_query: str,
    planned_list: Optional[PlannedItemList] = None,
    max_items: int = 100,
) -> List[PlannedItem]:
    return _default_source().get_tasks_by_filter(
        filter_query=filter_query, planned_list=planned_list, max_items=max_items
    )


def auto_complete_parent_tasks(
    tasks: List[PlannedItem],
    planned_list: Optional[PlannedItemList] = None,
) -> int:
    return _default_source().auto_complete_parent_tasks(
        tasks=tasks, planned_list=planned_list
    )


def create_task(
    content: str,
    project_id: Optional[str] = None,
    due_string: Optional[str] = None,
    priority: int = 1,
    labels: Optional[List[str]] = None,
) -> Optional[PlannedItem]:
    return _default_source().create_task(
        content=content,
        project_id=project_id,
        due_string=due_string,
        priority=priority,
        labels=labels,
    )