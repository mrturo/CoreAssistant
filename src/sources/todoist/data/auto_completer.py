# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=broad-except
from __future__ import annotations

from typing import Dict, List, Set

from src.model import ItemStatus, PlannedItem
from src.sources.todoist.data.updater import TodoistTaskUpdater


class TodoistTaskAutoCompleter:
    def __init__(self, task_updater: TodoistTaskUpdater):
        self.task_updater = task_updater
        self._processed_tasks: Set[str] = set()

    def process_tasks_for_auto_completion(self, tasks: List[PlannedItem]) -> int:
        self._processed_tasks.clear()
        completed_count = 0

        tasks_by_id = self._build_task_index(tasks)

        for task in tasks:
            if task.is_root() and task.id and task.id not in self._processed_tasks:
                completed_count += self._process_task_recursive(task, tasks_by_id)

        print(f"Todoist auto-completion finished. Tasks automatically completed: {completed_count}")
        return completed_count

    def _build_task_index(self, tasks: List[PlannedItem]) -> Dict[str, PlannedItem]:
        index = {}

        def add_task_to_index(task: PlannedItem):
            if task.id:
                index[task.id] = task
            for subtask in task.subitems:
                add_task_to_index(subtask)

        for task in tasks:
            add_task_to_index(task)

        return index

    def _process_task_recursive(
        self, task: PlannedItem, tasks_by_id: Dict[str, PlannedItem]
    ) -> int:
        if not task.id or task.id in self._processed_tasks:
            return 0

        self._processed_tasks.add(task.id)
        completed_count = 0

        for subtask in task.subitems:
            completed_count += self._process_task_recursive(subtask, tasks_by_id)

        if self._should_auto_complete_task(task):
            success = self._mark_task_completed(task)
            if success:
                completed_count += 1
                task.status = ItemStatus.COMPLETED
                print(f"Todoist task '{task.title}' (ID: {task.id}) auto-completed successfully")

        return completed_count

    def _should_auto_complete_task(self, task: PlannedItem) -> bool:
        if task.status == ItemStatus.COMPLETED:
            return False

        if not task.subitems:
            return False

        return self._all_subtasks_completed(task)

    def _all_subtasks_completed(self, task: PlannedItem) -> bool:
        if not task.subitems:
            return True

        for subtask in task.subitems:
            if subtask.status != ItemStatus.COMPLETED:
                return False
            if not self._all_subtasks_completed(subtask):
                return False

        return True

    def _mark_task_completed(self, task: PlannedItem) -> bool:
        if not task.id:
            print(f"Attempting to mark Todoist task without ID as completed: {task.title}")
            return False

        try:
            return self.task_updater.mark_task_as_completed(task.id)
        except Exception as exc:
            print(f"Error marking Todoist task as completed {task.title} (ID: {task.id}): {exc}")
            return False