# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import os
import sys
from typing import List

from src.model import PlannedItem
from src.planned_item.orchestration.data_fetcher import DataFetcher
from src.planned_item.orchestration.list_manager import ListManager
from src.planned_item.presenters.console_presenter import ConsolePresenter


def main_google_only() -> None:
    print("🔍 Getting data from Google Tasks and Google Calendar...")
    
    list_manager = ListManager()
    task_lists = list_manager.get_task_lists()
    calendars_list = list_manager.get_calendars_list()
    data_fetcher = DataFetcher()
    
    tasks: List[PlannedItem] = data_fetcher.get_pending_tasks_with_auto_complete(
        task_lists
    )
    events: List[PlannedItem] = data_fetcher.get_upcoming_events(calendars_list)
    all_items: List[PlannedItem] = PlannedItem.sort(tasks + events)
    
    print(f"📊 Google Tasks: {len(tasks)} tasks, Google Calendar: {len(events)} events")
    
    grouped_items = PlannedItem.time_grouper(all_items)
    presenter = ConsolePresenter()
    presenter.print_planned_items(grouped_items)


def main_todoist_only() -> None:
    print("🔍 Getting data from Todoist...")
    
    list_manager = ListManager()
    todoist_projects = list_manager.get_todoist_projects()
    calendars_list = list_manager.get_calendars_list()
    data_fetcher = DataFetcher()
    
    tasks: List[PlannedItem] = data_fetcher.get_todoist_pending_tasks_with_auto_complete(
        todoist_projects
    )
    events: List[PlannedItem] = data_fetcher.get_upcoming_events(calendars_list)
    all_items: List[PlannedItem] = PlannedItem.sort(tasks + events)
    
    print(f"📊 Todoist: {len(tasks)} tasks, Google Calendar: {len(events)} events")
    
    grouped_items = PlannedItem.time_grouper(all_items)
    presenter = ConsolePresenter()
    presenter.print_planned_items(grouped_items)


def main_all_sources() -> None:
    print("🔍 Getting data from all sources...")
    
    list_manager = ListManager()
    calendars_list = list_manager.get_calendars_list()
    data_fetcher = DataFetcher()
    
    tasks: List[PlannedItem] = data_fetcher.get_all_pending_tasks_with_auto_complete()
    events: List[PlannedItem] = data_fetcher.get_upcoming_events(calendars_list)
    all_items: List[PlannedItem] = PlannedItem.sort(tasks + events)
    
    google_tasks = [t for t in tasks if t.data_source and "google" in t.data_source.value]
    todoist_tasks = [t for t in tasks if t.data_source and "todoist" in t.data_source.value]
    
    print(f"📊 Google Tasks: {len(google_tasks)}, Todoist: {len(todoist_tasks)}, "
          f"Google Calendar: {len(events)} events")
    
    grouped_items = PlannedItem.time_grouper(all_items)
    presenter = ConsolePresenter()
    presenter.print_planned_items(grouped_items)


def main() -> None:
    todoist_token = os.getenv("TODOIST_API_TOKEN")
    todoist_available = todoist_token is not None and len(todoist_token.strip()) > 0
    
    mode = os.getenv("COREASSISTANT_MODE", "auto").lower()
    
    try:
        if mode == "google":
            main_google_only()
        elif mode == "todoist":
            if not todoist_available:
                print("❌ TODOIST_API_TOKEN not configured. Using Google only.")
                main_google_only()
            else:
                main_todoist_only()
        elif mode == "all":
            if not todoist_available:
                print("⚠️  TODOIST_API_TOKEN not configured. Using Google only.")
                main_google_only()
            else:
                main_all_sources()
        else:
            if todoist_available:
                print("✅ Todoist detected. Using all sources.")
                main_all_sources()
            else:
                print("ℹ️  Only Google configured. To add Todoist, configure TODOIST_API_TOKEN.")
                main_google_only()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have the correct credentials configured:")
        print("- Google: config/gcp/credentials.json and token.json")
        print("- Todoist: TODOIST_API_TOKEN in .env")
        sys.exit(1)


if __name__ == "__main__":
    main()