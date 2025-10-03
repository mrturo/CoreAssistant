# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Any, Mapping, Optional

from src.model import DataSource, ItemStatus, ItemType
from src.model.core.planned_item import UNTITLED

from .base import FieldSpec, GoogleBaseMapper, MappingError, as_bool

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


class GoogleCalendarEventsMapper(GoogleBaseMapper):
    def __init__(self):
        field_specs = {
            "kind": FieldSpec("kind", transform=lambda v: v, default="calendar#event"),
            "id": FieldSpec("id", transform=lambda v: v, required=True),
            "etag": FieldSpec("etag", transform=lambda v: v),
            "self_link": FieldSpec("selfLink", transform=lambda v: v),
            "web_view_link": FieldSpec("htmlLink", transform=lambda v: v),
            "title": FieldSpec(
                "summary", transform=lambda v: v or UNTITLED, default=UNTITLED
            ),
            "notes": FieldSpec("description", transform=lambda v: v),
            "status": FieldSpec("status", transform=ItemStatus.from_api),
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
            "type": FieldSpec("type", transform=lambda v: ItemType.EVENT),
            "planned_item_list": FieldSpec(
                "plannedItemList", transform=lambda v: None, default=None
            ),
            "data_source": FieldSpec(
                "data_source",
                transform=lambda v: DataSource.GOOGLE_CALENDAR,
                default=DataSource.GOOGLE_CALENDAR,
            ),
        }
        super().__init__(field_specs)
