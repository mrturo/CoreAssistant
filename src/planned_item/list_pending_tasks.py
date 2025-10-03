# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

import datetime
import sys
from collections.abc import Collection

from src.model.planned_item import PlannedItem
from src.model.planned_item_group import PlannedItemGroup
from src.model.planned_item_list import (PlannedItemList,
                                         PlannedItemListMetadata)
from src.planned_item.render import ItemLike, TextTreeRenderer
from src.sources import gcp
from src.util.parameters import ParameterLoader
from src.util.period import Period

params = ParameterLoader()
now: datetime = params.get("NOW")
today: datetime.date = params.get("TODAY")
ignored_lists: list[str] = params.get("IGNORED_LISTS")


def get_pending_tasks() -> list[PlannedItem]:
    task_lists: list[dict[str, str | None]] = []
    pending_tasks: list[PlannedItem] = []
    try:
        task_lists = gcp.list_tasks()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    if not task_lists or len(task_lists) == 0:
        print("No task lists found.", file=sys.stderr)
    else:
        for t in task_lists:
            try:
                if t is None:
                    raise ValueError("Task list is None.")
                list_id: any = t.get("id")
                if t is None or list_id is None or t.get("title") is None:
                    raise ValueError("Task list is missing required fields.")
                if not isinstance(list_id, str) or not isinstance(t.get("title"), str):
                    raise ValueError("Task list fields have incorrect types.")
                list_id = list_id.strip()
                if len(list_id) == 0 or len(t.get("title").strip()) == 0:
                    raise ValueError("Task list fields cannot be empty.")
                if list_id not in ignored_lists:
                    planned_item_list = PlannedItemList(
                        kind="tasklist",
                        id=list_id,
                        name=t.get("title"),
                        metadata=PlannedItemListMetadata(
                            access_role=t.get("accessRole"),
                            updated=t.get("updated"),
                            self_link=t.get("selfLink"),
                        ),
                    )
                    pending_tasks += gcp.get_pending_tasks(
                        planned_list=planned_item_list
                    )
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
    return pending_tasks


def get_upcoming_events() -> list[PlannedItem]:
    list_calendars: list[dict[str, str | None]] = []
    upcoming_events: list[PlannedItem] = []
    try:
        list_calendars = gcp.list_calendars()
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    if not list_calendars or len(list_calendars) == 0:
        print("No calendars found.", file=sys.stderr)
    else:
        for calendar in list_calendars:
            try:
                if calendar is None:
                    raise ValueError("Calendar is None.")
                list_id: any = calendar.get("id")
                if (
                    calendar is None
                    or list_id is None
                    or calendar.get("summary") is None
                ):
                    raise ValueError("Calendar is missing required fields.")
                if not isinstance(list_id, str) or not isinstance(
                    calendar.get("summary"), str
                ):
                    raise ValueError("Calendar fields have incorrect types.")
                list_id = list_id.strip()
                if len(list_id) == 0 or len(calendar.get("summary").strip()) == 0:
                    raise ValueError("Calendar fields cannot be empty.")
                if list_id not in ignored_lists:
                    planned_item_list = PlannedItemList(
                        kind="calendar",
                        id=calendar.get("id"),
                        name=calendar.get("summary"),
                        metadata=PlannedItemListMetadata(
                            access_role=calendar.get("accessRole"),
                            updated=calendar.get("updated"),
                            self_link=calendar.get("selfLink"),
                            time_zone=calendar.get("timeZone"),
                            primary=calendar.get("primary", False),
                        ),
                    )
                    upcoming_events += gcp.get_upcoming_events(
                        planned_list=planned_item_list
                    )
            except ValueError as exc:
                print(f"Error: {exc}", file=sys.stderr)
    return upcoming_events


def is_valid_group(group: any, period: any, group_items: any) -> bool:
    if not group or not isinstance(group, PlannedItemGroup):
        return False
    if (
        not period
        or not isinstance(period, Period)
        or period.start is None
        or not isinstance(period.start, datetime.date)
    ):
        return False
    if (
        not group_items
        or not isinstance(group_items, Collection)
        or len(group_items) == 0
        or not all(isinstance(x, ItemLike) for x in group_items)
    ):
        return False
    return True


def print_planned_items(all_groups: list[PlannedItem]) -> None:
    renderer = TextTreeRenderer(indent_step=2)
    first_group = True
    for group, (period, group_items) in all_groups.items():
        if not is_valid_group(group, period, group_items):
            continue
        if not first_group:
            print()
        else:
            first_group = False
        print(f"=== {group.label} ===")
        if group == PlannedItemGroup.DUED:
            print(f"Before {today}")
        elif group == PlannedItemGroup.FUTURE:
            print(f"Starting from {period.start}")
        elif group not in [PlannedItemGroup.ON_GOING]:
            name: str = "Date"
            if period.duration > 1:
                name = "Period"
            if (
                group
                in [
                    PlannedItemGroup.TODAY,
                    PlannedItemGroup.TOMORROW,
                    PlannedItemGroup.THIS_FRIDAY,
                    PlannedItemGroup.THIS_SUNDAY,
                ]
                and period.start == period.end
            ):
                print(f"{name}: {period.start}")
            elif group in [
                PlannedItemGroup.REST_OF_THIS_WEEK,
                PlannedItemGroup.THIS_WEEKEND,
                PlannedItemGroup.NEXT_WEEK,
                PlannedItemGroup.REST_OF_THIS_MONTH,
                PlannedItemGroup.NEXT_MONTH,
            ]:
                print(f"{name}: {period.start} → {period.end}")
        print(renderer.render(group_items))


if __name__ == "__main__":
    tasks: list[PlannedItem] = get_pending_tasks()
    events: list[PlannedItem] = get_upcoming_events()
    all_items: list[PlannedItem] = PlannedItem.sort(tasks + events)
    print_planned_items(PlannedItem.time_grouper(all_items))
