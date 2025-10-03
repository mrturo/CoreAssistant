# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=broad-except
from __future__ import annotations

from typing import Any, Dict, Optional

from src.model.list import PlannedItemList
from src.sources.todoist.services.client import TodoistClient


class TodoistTaskUpdater:
    def __init__(self, client: TodoistClient, planned_list: PlannedItemList):
        self.client = client
        self.planned_list = planned_list

    def mark_task_as_completed(self, task_id: str) -> bool:
        try:
            success = self.client.complete_task(task_id)
            if success:
                print(f"Task {task_id} marked as completed successfully in Todoist")
            return success

        except Exception as exc:
            print(f"Error marking Todoist task {task_id} as completed: {exc}")
            return False

    def get_task_details(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            tasks = self.client.get_tasks()
            for task in tasks:
                if task.get("id") == task_id:
                    return task
            return None
        except Exception as exc:
            print(f"Error getting Todoist task details {task_id}: {exc}")
            return None

    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if self.planned_list.id and self.planned_list.id.isdigit():
                task_data["project_id"] = self.planned_list.id
            
            return self.client.create_task(task_data)
        except Exception as exc:
            print(f"Error creating Todoist task: {exc}")
            return None

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            return self.client.update_task(task_id, task_data)
        except Exception as exc:
            print(f"Error updating Todoist task {task_id}: {exc}")
            return None