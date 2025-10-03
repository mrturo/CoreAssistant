# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional
from zoneinfo import ZoneInfo

from src.common.data.parameters import ParameterLoader
from src.model import PlannedItemList

from .config import TaskQueryConfig


class TaskEnricher:
    def __init__(self, config: TaskQueryConfig, planned_list: PlannedItemList):
        params = ParameterLoader()
        self.tzinfo: ZoneInfo = params.get("TZINFO")
        self.config = config
        self.planned_list = planned_list

    def _parse_due_utc(self, raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))

    def _iso_utc(self, dt: datetime) -> str:
        return dt.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

    def enrich_items(self, items: List[dict]) -> List[dict]:
        enriched = []
        for item in items:
            due_utc = self._parse_due_utc(item.get("due"))
            if not due_utc:
                if self.config.filter_local_date is None:
                    enriched.append(item)
                continue
            local_date = due_utc.astimezone(self.tzinfo).date()
            if (
                self.config.filter_local_date is not None
                and local_date != self.config.filter_local_date
            ):
                continue
            enriched.append(item)
            if self.config.show_tz_shadow and local_date != due_utc.date():
                shadow = self._create_timezone_shadow(item, local_date)
                enriched.append(shadow)
        return enriched

    def _create_timezone_shadow(self, item: dict, local_date: date) -> dict:
        local_midnight = datetime.combine(local_date, time.min, tzinfo=self.tzinfo)
        shadow = dict(item)
        shadow["id"] = f'{item["id"]}#tzshadow:{self.tzinfo.key}'
        shadow["due"] = self._iso_utc(local_midnight)
        shadow["title"] = f'{item.get("title", "")} (local)'
        shadow["plannedItemList"] = self.planned_list
        return shadow
