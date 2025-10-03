# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Dict, List, Optional

from src.common.hierarchy.hierarchy_builder import HierarchyBuilder
from src.common.hierarchy.parent_policy import ParentPolicy
from src.model import ItemStatus, PlannedItem, PlannedItemList
from src.sources.todoist.auth.settings import TodoistAuthSettings
from src.sources.todoist.data.auto_completer import TodoistTaskAutoCompleter
from src.sources.todoist.data.fetcher import TodoistTaskFetcher
from src.sources.todoist.data.updater import TodoistTaskUpdater
from src.sources.todoist.mappers.tasks import TodoistTasksMapper
from src.sources.todoist.services.client import TodoistClient

DEFAULT_PROJECT_ID = "inbox"


class TodoistPlannedSource:
    def __init__(self, auth_settings: Optional[TodoistAuthSettings] = None) -> None:
        self._auth_settings = auth_settings or TodoistAuthSettings()
        self._client = TodoistClient(self._auth_settings)

    def get_pending_tasks(
        self,
        planned_list: Optional[PlannedItemList] = None,
        max_items: int = 200,
    ) -> List[PlannedItem]:
        planned_list = planned_list or PlannedItemList(
            kind="todoist_project", id=DEFAULT_PROJECT_ID, name="Inbox"
        )
        
        fetcher = TodoistTaskFetcher(self._client, planned_list)
        fetcher.fetch_pending_tasks(max_items)
        
        builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
        tasks = builder.build(fetcher.all_items, TodoistTasksMapper())
        
        return [
            t for t in tasks 
            if t.is_root() and t.status == ItemStatus.NEEDS_ACTION
        ]

    def get_projects_list(self, max_items: int = 100) -> List[Dict[str, Optional[str]]]:
        try:
            projects = self._client.get_projects()
            results: List[Dict[str, Optional[str]]] = []
            
            for project in projects[:max_items]:
                results.append({
                    "id": str(project.get("id", "")),
                    "title": project.get("name", ""),
                    "color": project.get("color"),
                    "is_shared": project.get("is_shared", False),
                    "is_favorite": project.get("is_favorite", False),
                    "is_inbox_project": project.get("is_inbox_project", False),
                    "view_style": project.get("view_style", "list"),
                })
            return results
        except Exception as e:
            print(f"Error fetching Todoist projects: {e}")
            return []

    def get_labels_list(self, max_items: int = 100) -> List[Dict[str, Optional[str]]]:
        try:
            labels = self._client.get_labels()
            results: List[Dict[str, Optional[str]]] = []
            
            for label in labels[:max_items]:
                results.append({
                    "id": str(label.get("id", "")),
                    "title": label.get("name", ""),
                    "color": label.get("color"),
                    "is_favorite": label.get("is_favorite", False),
                })
            return results
        except Exception as e:
            print(f"Error fetching Todoist labels: {e}")
            return []

    def get_tasks_by_filter(
        self,
        filter_query: str,
        planned_list: Optional[PlannedItemList] = None,
        max_items: int = 100,
    ) -> List[PlannedItem]:
        planned_list = planned_list or PlannedItemList(
            kind="todoist_filter", id="filter", name=f"Filter: {filter_query}"
        )
        
        fetcher = TodoistTaskFetcher(self._client, planned_list)
        fetcher.fetch_tasks_by_filter(filter_query, max_items)
        
        builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
        tasks = builder.build(fetcher.all_items, TodoistTasksMapper())
        
        return [t for t in tasks if t.is_root()]

    def auto_complete_parent_tasks(
        self,
        tasks: List[PlannedItem],
        planned_list: Optional[PlannedItemList] = None,
    ) -> int:
        planned_list = planned_list or PlannedItemList(
            kind="todoist_project", id=DEFAULT_PROJECT_ID, name="Inbox"
        )
        
        updater = TodoistTaskUpdater(self._client, planned_list)
        auto_completer = TodoistTaskAutoCompleter(updater)
        
        return auto_completer.process_tasks_for_auto_completion(tasks)

    def create_task(
        self,
        content: str,
        project_id: Optional[str] = None,
        due_string: Optional[str] = None,
        priority: int = 1,
        labels: Optional[List[str]] = None,
    ) -> Optional[PlannedItem]:
        task_data = {
            "content": content,
            "project_id": project_id or DEFAULT_PROJECT_ID,
        }
        
        if due_string:
            task_data["due_string"] = due_string
        if priority > 1:
            task_data["priority"] = priority
        if labels:
            task_data["labels"] = labels
            
        try:
            raw_task = self._client.create_task(task_data)
            if raw_task:
                mapper = TodoistTasksMapper()
                return mapper.to_entity(raw_task)
            return None
        except Exception as e:
            print(f"Error creating Todoist task: {e}")
            return None