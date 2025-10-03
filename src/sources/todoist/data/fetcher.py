# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.model import PlannedItemList
from src.sources.todoist.services.client import TodoistClient


class TodoistTaskFetcher:
    def __init__(self, client: TodoistClient, planned_list: PlannedItemList):
        self.client = client
        self.planned_list = planned_list
        self.all_items: List[Dict[str, Any]] = []
        self.seen_ids: set = set()

    def _append_items(self, items: List[Dict[str, Any]]) -> None:
        for item in items:
            task_id = item.get("id")
            if task_id and task_id not in self.seen_ids:
                item["plannedItemList"] = self.planned_list
                self.all_items.append(item)
                self.seen_ids.add(task_id)

    def fetch_pending_tasks(self, max_items: int = 200) -> None:
        try:
            project_id = None
            if (self.planned_list.id and 
                self.planned_list.id != "inbox" and 
                self.planned_list.id.isdigit()):
                project_id = self.planned_list.id
            
            tasks = self.client.get_tasks(project_id=project_id)
            
            pending_tasks = [task for task in tasks if not task.get("is_completed", False)]
            
            if len(pending_tasks) > max_items:
                pending_tasks = pending_tasks[:max_items]
            
            self._append_items(pending_tasks)
            
        except Exception as e:
            print(f"Error fetching Todoist tasks: {e}")

    def fetch_completed_tasks(self, max_items: int = 50) -> None:
        try:
            project_id = None
            if (self.planned_list.id and 
                self.planned_list.id != "inbox" and 
                self.planned_list.id.isdigit()):
                project_id = self.planned_list.id
            
            all_tasks = self.client.get_tasks(project_id=project_id)
            completed_tasks = [task for task in all_tasks if task.get("is_completed", False)]
            
            completed_tasks = completed_tasks[:max_items]
            
            self._append_items(completed_tasks)
            
        except Exception as e:
            print(f"Error fetching completed Todoist tasks: {e}")

    def fetch_tasks_by_filter(self, filter_query: str, max_items: int = 100) -> None:
        try:
            tasks = self.client.get_tasks(filter_query=filter_query)
            
            if len(tasks) > max_items:
                tasks = tasks[:max_items]
            
            self._append_items(tasks)
            
        except Exception as e:
            print(f"Error fetching Todoist tasks with filter '{filter_query}': {e}")