# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.mappers.common_mappers import (BaseItemMapper, FieldSpec,
                                        MappingError, as_bool, identity,
                                        map_to_planned_item)
from src.model.planned_item import UNTITLED, PlannedItem
from src.model.planned_item_status import PlannedItemStatus
from src.model.planned_item_type import PlannedItemType

__all__ = ["GoogleTasksMapper", "MappingError"]


class GoogleTasksMapper(BaseItemMapper):

    _FIELD_SPECS: Mapping[str, FieldSpec] = MappingProxyType(
        {
            "kind": FieldSpec("kind"),
            "id": FieldSpec("id", required=True),
            "etag": FieldSpec("etag"),
            "self_link": FieldSpec("selfLink"),
            "web_view_link": FieldSpec("webViewLink"),
            "title": FieldSpec("title", default=UNTITLED),
            "notes": FieldSpec("notes"),
            "status": FieldSpec(
                "status", transform=PlannedItemStatus.from_api, default=None
            ),
            "start_raw": FieldSpec("due"),
            "end_raw": FieldSpec("completed"),
            "updated_raw": FieldSpec("updated"),
            "parent": FieldSpec("parent"),
            "position": FieldSpec("position"),
            "hidden": FieldSpec("hidden", transform=as_bool, default=False),
            "deleted": FieldSpec("deleted", transform=as_bool, default=False),
            "links": FieldSpec("links", transform=identity, default=None),
            "assignment_info": FieldSpec("assignmentInfo"),
            "type": FieldSpec("type", transform=lambda v: PlannedItemType.TASK),
            "planned_item_list": FieldSpec(
                "plannedItemList", transform=identity, default=None
            ),
        }
    )

    def to_entity(self, raw: Mapping[str, Any]) -> PlannedItem:
        return map_to_planned_item(raw, self._FIELD_SPECS)
