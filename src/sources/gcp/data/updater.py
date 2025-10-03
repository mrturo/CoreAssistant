# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=broad-except
from __future__ import annotations

from datetime import datetime
from typing import Optional

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

from src.model.list import PlannedItemList


class TaskUpdater:
    def __init__(self, service: Resource, planned_list: PlannedItemList):
        self.service = service
        self.planned_list = planned_list

    def mark_task_as_completed(self, task_id: str) -> bool:
        try:
            task_update = {
                "id": task_id,
                "status": "completed",
                "completed": datetime.utcnow().isoformat() + "Z",
            }

            self.service.tasks().update(
                tasklist=self.planned_list.id, task=task_id, body=task_update
            ).execute()

            print("Task %s marked as completed successfully", task_id)
            return True

        except HttpError as exc:
            print("Error marking task %s as completed: %s", task_id, exc)
            return False
        except Exception as exc:
            print("Unexpected error updating task %s: %s", task_id, exc)
            return False

    def get_task_details(self, task_id: str) -> Optional[dict]:
        try:
            task = (
                self.service.tasks()
                .get(tasklist=self.planned_list.id, task=task_id)
                .execute()
            )
            return task
        except HttpError as exc:
            print("Error getting task details %s: %s", task_id, exc)
            return None
        except Exception as exc:
            print("Unexpected error getting task %s: %s", task_id, exc)
            return None
