# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import List

from src.model import PlannedItem
from src.planned_item.orchestration.data_fetcher import DataFetcher
from src.planned_item.orchestration.list_manager import ListManager
from src.planned_item.presenters.console_presenter import ConsolePresenter
from src.sources.todoist import todoist


def basic_todoist_example() -> None:
    print("=== BASIC EXAMPLE: Todoist Tasks ===")
    
    list_manager = ListManager()
    todoist_projects = list_manager.get_todoist_projects()
    
    print(f"Projects found in Todoist: {len(todoist_projects)}")
    for project in todoist_projects:
        print(f"- {project.name} (ID: {project.id})")
    
    data_fetcher = DataFetcher()
    tasks: List[PlannedItem] = data_fetcher.get_todoist_pending_tasks_with_auto_complete(
        todoist_projects
    )
    
    print(f"\nPending tasks: {len(tasks)}")
    if tasks:
        all_items: List[PlannedItem] = PlannedItem.sort(tasks)
        grouped_items = PlannedItem.time_grouper(all_items)
        presenter = ConsolePresenter()
        presenter.print_planned_items(grouped_items)


def todoist_filters_example() -> None:
    print("=== EXAMPLE: Todoist Filters ===")
    
    filters = [
        "today",
        "overdue",
        "p1",
        "no date",
        "@work",
    ]
    
    for filter_name in filters:
        try:
            tasks = todoist.get_tasks_by_filter(filter_name, max_items=5)
            print(f"\nFilter '{filter_name}': {len(tasks)} tasks")
            for task in tasks[:3]:
                print(f"  - {task.title}")
        except Exception as e:
            print(f"  Error with filter '{filter_name}': {e}")


def create_task_example() -> None:
    print("=== EXAMPLE: Create task in Todoist ===")
    
    try:
        new_task = todoist.create_task(
            content="Task created from CoreAssistant",
            due_string="tomorrow",
            priority=2,
            labels=["test"]
        )
        
        if new_task:
            print(f"✅ Task created: {new_task.title}")
            print(f"   ID: {new_task.id}")
            print(f"   Due date: {new_task.start_raw}")
        else:
            print("❌ Could not create task")
            
    except Exception as e:
        print(f"❌ Error creating task: {e}")


def all_sources_example() -> None:
    print("=== EXAMPLE: All sources (Google + Todoist) ===")
    
    data_fetcher = DataFetcher()
    all_tasks = data_fetcher.get_all_pending_tasks_with_auto_complete()
    
    print(f"Total pending tasks from all sources: {len(all_tasks)}")
    
    google_tasks = [t for t in all_tasks if t.data_source and "google" in t.data_source.value]
    todoist_tasks = [t for t in all_tasks if t.data_source and "todoist" in t.data_source.value]
    
    print(f"Google Tasks: {len(google_tasks)}")
    print(f"Todoist: {len(todoist_tasks)}")
    
    if all_tasks:
        all_items: List[PlannedItem] = PlannedItem.sort(all_tasks)
        grouped_items = PlannedItem.time_grouper(all_items)
        presenter = ConsolePresenter()
        presenter.print_planned_items(grouped_items)


def main() -> None:
    try:
        basic_todoist_example()
        print("\n" + "="*50 + "\n")
        
        todoist_filters_example()
        print("\n" + "="*50 + "\n")
        
        all_sources_example()
        
    except Exception as e:
        print(f"❌ General error: {e}")
        print("Make sure you have TODOIST_API_TOKEN configured in your .env")


if __name__ == "__main__":
    main()