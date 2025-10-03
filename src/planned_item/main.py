# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.model import PlannedItem
from src.planned_item.orchestration.data_fetcher import DataFetcher
from src.planned_item.orchestration.list_manager import ListManager
from src.planned_item.presenters.console_presenter import ConsolePresenter


def main() -> None:
    list_manager = ListManager()
    task_lists = list_manager.get_task_lists()
    calendars_list = list_manager.get_calendars_list()
    data_fetcher = DataFetcher()
    tasks: List[PlannedItem] = data_fetcher.get_pending_tasks_with_auto_complete(
        task_lists
    )
    events: List[PlannedItem] = data_fetcher.get_upcoming_events(calendars_list)
    all_items: List[PlannedItem] = PlannedItem.sort(tasks + events)
    grouped_items = PlannedItem.time_grouper(all_items)
    presenter = ConsolePresenter()
    presenter.print_planned_items(grouped_items)


if __name__ == "__main__":
    main()
