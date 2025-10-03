# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import sys
from typing import List

from src.common.data.list_processing import (validate_and_create_calendar,
                                             validate_and_create_task_list,
                                             validate_and_create_todoist_project)
from src.common.data.parameters import ParameterLoader
from src.model import PlannedItem, PlannedItemList
from src.sources.gcp import gcp
from src.sources.todoist import todoist

params = ParameterLoader()
ignored_lists: list[str] = params.get("IGNORED_LISTS")


def _fetch_from_lists(lists: List[PlannedItemList], list_type_name: str, fetch_func):
    result: List[PlannedItem] = []
    if not lists or len(lists) == 0:
        print(f"No {list_type_name} found.")
    else:
        for item_list in lists:
            result += fetch_func(planned_list=item_list)
    return result


def _apply_auto_complete_to_tasks(
    tasks: List[PlannedItem], task_lists: List[PlannedItemList], fetch_func, auto_complete_func
) -> List[PlannedItem]:
    total_auto_completed = 0
    for task_list in task_lists:
        list_tasks = [
            task
            for task in tasks
            if task.planned_item_list and task.planned_item_list.id == task_list.id
        ]

        if list_tasks:
            auto_completed = auto_complete_func(list_tasks, task_list)
            total_auto_completed += auto_completed

    if total_auto_completed > 0:
        print(f"✅ {total_auto_completed} parent tasks were auto-completed")
        tasks = _fetch_from_lists(task_lists, "task lists", fetch_func)

    return tasks


def get_task_lists() -> List[PlannedItemList]:
    raw_task_lists: list[dict[str, str | None]] = []
    task_lists: list[PlannedItemList] = []
    try:
        raw_task_lists = gcp.get_tasks_lists()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    if raw_task_lists or len(raw_task_lists) > 0:
        for task_list in raw_task_lists:
            result = validate_and_create_task_list(task_list, ignored_lists)
            if result:
                task_lists.append(result)
    return task_lists


def get_calendars_list() -> List[PlannedItemList]:
    raw_calendar_list: list[dict[str, str | None]] = []
    calendar_list: list[PlannedItemList] = []
    try:
        raw_calendar_list = gcp.get_calendars_list()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    if raw_calendar_list or len(raw_calendar_list) > 0:
        for raw_calendar in raw_calendar_list:
            result = validate_and_create_calendar(raw_calendar, ignored_lists)
            if result:
                calendar_list.append(result)
    return calendar_list


def get_pending_tasks() -> List[PlannedItem]:
    task_lists: List[PlannedItemList] = get_task_lists()
    return _fetch_from_lists(task_lists, "task lists", gcp.get_pending_tasks)


def get_pending_tasks_with_auto_complete() -> List[PlannedItem]:
    task_lists: List[PlannedItemList] = get_task_lists()
    tasks = _fetch_from_lists(task_lists, "task lists", gcp.get_pending_tasks)

    return _apply_auto_complete_to_tasks(tasks, task_lists, gcp.get_pending_tasks, gcp.auto_complete_parent_tasks)


def get_upcoming_events() -> List[PlannedItem]:
    calendars_list = get_calendars_list()
    return _fetch_from_lists(calendars_list, "calendars", gcp.get_upcoming_events)


def get_todoist_projects_list() -> List[PlannedItemList]:
    raw_projects: list[dict[str, str | None]] = []
    projects: list[PlannedItemList] = []
    try:
        raw_projects = todoist.get_projects_list()
    except ValueError as exc:
        print(f"Error fetching Todoist projects: {exc}", file=sys.stderr)
    
    if raw_projects:
        for project in raw_projects:
            result = validate_and_create_todoist_project(project, ignored_lists)
            if result:
                projects.append(result)
    return projects


def get_todoist_pending_tasks() -> List[PlannedItem]:
    project_lists: List[PlannedItemList] = get_todoist_projects_list()
    return _fetch_from_lists(project_lists, "Todoist projects", todoist.get_pending_tasks)


def get_todoist_pending_tasks_with_auto_complete() -> List[PlannedItem]:
    project_lists: List[PlannedItemList] = get_todoist_projects_list()
    tasks = _fetch_from_lists(project_lists, "Todoist projects", todoist.get_pending_tasks)

    return _apply_auto_complete_to_tasks(
        tasks, project_lists, todoist.get_pending_tasks, todoist.auto_complete_parent_tasks
    )


def get_all_pending_tasks() -> List[PlannedItem]:
    google_tasks = get_pending_tasks()
    todoist_tasks = get_todoist_pending_tasks()
    return google_tasks + todoist_tasks


def get_all_pending_tasks_with_auto_complete() -> List[PlannedItem]:
    google_tasks = get_pending_tasks_with_auto_complete()
    todoist_tasks = get_todoist_pending_tasks_with_auto_complete()
    return google_tasks + todoist_tasks
