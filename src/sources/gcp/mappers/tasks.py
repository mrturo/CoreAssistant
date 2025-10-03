# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from src.model import DataSource, ItemStatus, ItemType
from src.model.core.planned_item import UNTITLED

from .base import FieldSpec, GoogleBaseMapper, MappingError, as_bool, identity

__all__ = ["GoogleTasksMapper", "MappingError"]


class GoogleTasksMapper(GoogleBaseMapper):
    def __init__(self):
        field_specs = {
            "kind": FieldSpec("kind"),
            "id": FieldSpec("id", required=True),
            "etag": FieldSpec("etag"),
            "self_link": FieldSpec("selfLink"),
            "web_view_link": FieldSpec("webViewLink"),
            "title": FieldSpec("title", default=UNTITLED),
            "notes": FieldSpec("notes"),
            "status": FieldSpec("status", transform=ItemStatus.from_api, default=None),
            "start_raw": FieldSpec("due"),
            "end_raw": FieldSpec("completed"),
            "updated_raw": FieldSpec("updated"),
            "parent": FieldSpec("parent"),
            "position": FieldSpec("position"),
            "hidden": FieldSpec("hidden", transform=as_bool, default=False),
            "deleted": FieldSpec("deleted", transform=as_bool, default=False),
            "links": FieldSpec("links", transform=identity, default=None),
            "assignment_info": FieldSpec("assignmentInfo"),
            "type": FieldSpec("type", transform=lambda v: ItemType.TASK),
            "planned_item_list": FieldSpec(
                "plannedItemList", transform=identity, default=None
            ),
            "data_source": FieldSpec(
                "data_source",
                transform=lambda v: DataSource.GOOGLE_TASK,
                default=DataSource.GOOGLE_TASK,
            ),
        }
        super().__init__(field_specs)
