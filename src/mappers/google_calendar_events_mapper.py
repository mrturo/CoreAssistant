# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, Optional

from src.mappers.common_mappers import (BaseItemMapper, FieldSpec,
                                        MappingError, as_bool,
                                        map_to_planned_item)
from src.model.planned_item import UNTITLED, PlannedItem
from src.model.planned_item_status import PlannedItemStatus
from src.model.planned_item_type import PlannedItemType

__all__ = ["GoogleCalendarEventsMapper", "MappingError"]


def _to_iso_start(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return value.get("dateTime") or value.get("date")
    return None


def _to_iso_end(value: Any) -> Optional[str]:
    return _to_iso_start(value)


class GoogleCalendarEventsMapper(BaseItemMapper):

    _FIELD_SPECS: Mapping[str, FieldSpec] = MappingProxyType(
        {
            "kind": FieldSpec("kind", transform=lambda v: v, default="calendar#event"),
            "id": FieldSpec("id", transform=lambda v: v, required=True),
            "etag": FieldSpec("etag", transform=lambda v: v),
            "self_link": FieldSpec("selfLink", transform=lambda v: v),
            "web_view_link": FieldSpec("htmlLink", transform=lambda v: v),
            "title": FieldSpec(
                "summary", transform=lambda v: v or UNTITLED, default=UNTITLED
            ),
            "notes": FieldSpec("description", transform=lambda v: v),
            "status": FieldSpec("status", transform=PlannedItemStatus.from_api),
            "start_raw": FieldSpec("start", transform=_to_iso_start),
            "end_raw": FieldSpec("end", transform=_to_iso_end),
            "updated_raw": FieldSpec("updated", transform=lambda v: v),
            "parent": FieldSpec("parent", transform=lambda v: None, default=None),
            "position": FieldSpec("position", transform=lambda v: None, default=None),
            "hidden": FieldSpec("hidden", transform=as_bool, default=False),
            "deleted": FieldSpec(
                "status",
                transform=lambda v: str(v).lower() == "cancelled",
                default=False,
            ),
            "links": FieldSpec("attachments", transform=lambda v: None, default=None),
            "assignment_info": FieldSpec(
                "creator", transform=lambda v: None, default=None
            ),
            "type": FieldSpec("type", transform=lambda v: PlannedItemType.EVENT),
            "planned_item_list": FieldSpec(
                "plannedItemList", transform=lambda v: None, default=None
            ),
        }
    )

    def to_entity(self, raw: Mapping[str, Any]) -> PlannedItem:
        return map_to_planned_item(raw, self._FIELD_SPECS)
