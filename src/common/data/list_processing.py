# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import sys
from typing import Any

from src.model import PlannedItemList, PlannedItemListMetadata
from src.model.validation import is_valid_group


def validate_and_create_task_list(
    task_list_data: dict[str, Any], ignored_lists: list[str]
) -> PlannedItemList | None:
    try:
        if (
            task_list_data is None
            or task_list_data.get("id") is None
            or task_list_data.get("title") is None
        ):
            raise ValueError("Task list is missing required fields.")
        if not isinstance(task_list_data.get("id"), str) or not isinstance(
            task_list_data.get("title"), str
        ):
            raise ValueError("Task list fields have incorrect types.")
        if (
            len(task_list_data.get("id").strip()) == 0
            or len(task_list_data.get("title").strip()) == 0
        ):
            raise ValueError("Task list fields cannot be empty.")
        list_id = task_list_data.get("id").strip()
        if list_id not in ignored_lists:
            return PlannedItemList(
                kind="tasklist",
                id=list_id,
                name=task_list_data.get("title"),
                metadata=PlannedItemListMetadata(
                    access_role=task_list_data.get("accessRole"),
                    updated=task_list_data.get("updated"),
                    self_link=task_list_data.get("selfLink"),
                ),
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    return None


def validate_and_create_calendar(
    calendar_data: dict[str, Any], ignored_lists: list[str]
) -> PlannedItemList | None:
    try:
        if (
            calendar_data is None
            or calendar_data.get("id") is None
            or calendar_data.get("summary") is None
        ):
            raise ValueError("Calendar is missing required fields.")
        if not isinstance(calendar_data.get("id"), str) or not isinstance(
            calendar_data.get("summary"), str
        ):
            raise ValueError("Calendar fields have incorrect types.")
        if (
            len(calendar_data.get("id").strip()) == 0
            or len(calendar_data.get("summary").strip()) == 0
        ):
            raise ValueError("Calendar fields cannot be empty.")
        calendar_id = calendar_data.get("id").strip()
        if calendar_id not in ignored_lists:
            return PlannedItemList(
                kind="calendar",
                id=calendar_id,
                name=calendar_data.get("summary"),
                metadata=PlannedItemListMetadata(
                    access_role=calendar_data.get("accessRole"),
                    updated=calendar_data.get("updated"),
                    self_link=calendar_data.get("selfLink"),
                    time_zone=calendar_data.get("timeZone"),
                    primary=calendar_data.get("primary", False),
                ),
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    return None


def validate_and_create_todoist_project(
    project_data: dict[str, Any], ignored_lists: list[str]
) -> PlannedItemList | None:
    try:
        if (
            project_data is None
            or project_data.get("id") is None
            or project_data.get("title") is None
        ):
            raise ValueError("Todoist project is missing required fields.")
        if not isinstance(project_data.get("id"), str) or not isinstance(
            project_data.get("title"), str
        ):
            raise ValueError("Todoist project fields have incorrect types.")
        if (
            len(project_data.get("id").strip()) == 0
            or len(project_data.get("title").strip()) == 0
        ):
            raise ValueError("Todoist project fields cannot be empty.")
        
        project_id = project_data.get("id").strip()
        if project_id not in ignored_lists:
            return PlannedItemList(
                kind="todoist_project",
                id=project_id,
                name=project_data.get("title"),
                metadata=PlannedItemListMetadata(
                    access_role=None,
                    updated=None,
                    self_link=None,
                    time_zone=None,
                    primary=project_data.get("is_inbox_project", False),
                ),
            )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    return None


__all__ = [
    "is_valid_group",
    "validate_and_create_task_list",
    "validate_and_create_calendar",
    "validate_and_create_todoist_project",
]
