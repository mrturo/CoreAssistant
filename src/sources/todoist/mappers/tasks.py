# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Any, Dict, Mapping

from src.model import DataSource, ItemStatus, ItemType
from src.model.core.planned_item import UNTITLED
from src.sources.gcp.mappers.base import (
    BaseItemMapper, FieldSpec, GoogleBaseMapper, as_bool
)

__all__ = ["TodoistTasksMapper"]


def _convert_todoist_priority(priority: int) -> int:
    return 5 - priority if priority else 4


def _convert_todoist_status(is_completed: bool) -> ItemStatus:
    return ItemStatus.COMPLETED if is_completed else ItemStatus.NEEDS_ACTION


class TodoistTasksMapper(GoogleBaseMapper):
    def __init__(self):
        field_specs = {
            "kind": FieldSpec("kind", default="todoist#task"),
            "id": FieldSpec("id", required=True),
            "etag": FieldSpec("etag", default=None),
            "self_link": FieldSpec("url", default=None),
            "web_view_link": FieldSpec("url", default=None),
            "title": FieldSpec("content", default=UNTITLED),
            "notes": FieldSpec("description", default=None),
            "status": FieldSpec(
                "is_completed", 
                transform=_convert_todoist_status, 
                default=ItemStatus.NEEDS_ACTION
            ),
            "start_raw": FieldSpec("due.datetime", default=None),
            "end_raw": FieldSpec("completed_at", default=None),
            "updated_raw": FieldSpec("created_at", default=None),
            "parent": FieldSpec("parent_id", default=None),
            "position": FieldSpec("order", transform=str, default=None),
            "hidden": FieldSpec("hidden", transform=as_bool, default=False),
            "deleted": FieldSpec("deleted", transform=as_bool, default=False),
            "links": FieldSpec("links", default=None),
            "assignment_info": FieldSpec("assignee_id", default=None),
            "type": FieldSpec("type", transform=lambda v: ItemType.TASK),
            "planned_item_list": FieldSpec(
                "plannedItemList", transform=lambda v: v, default=None
            ),
            "data_source": FieldSpec(
                "data_source",
                transform=lambda v: DataSource.TODOIST,
                default=DataSource.TODOIST,
            ),
            "priority": FieldSpec("priority", transform=_convert_todoist_priority, default=4),
            "project_id": FieldSpec("project_id", default=None),
            "section_id": FieldSpec("section_id", default=None),
            "labels": FieldSpec("labels", default=None),
        }
        super().__init__(field_specs)

    def to_entity(self, raw: Mapping[str, Any]) -> Any:
        processed_raw = dict(raw)
        
        due_info = raw.get("due")
        if due_info:
            if isinstance(due_info, dict):
                due_datetime = due_info.get("datetime") or due_info.get("date")
                if due_datetime:
                    processed_raw["due.datetime"] = due_datetime
        
        return super().to_entity(processed_raw)