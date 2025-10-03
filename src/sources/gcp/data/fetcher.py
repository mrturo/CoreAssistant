# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import re
from datetime import datetime
from typing import List

from googleapiclient.discovery import Resource

from src.model import PlannedItemList


class TaskFetcher:
    def __init__(self, service: Resource, planned_list: PlannedItemList):
        self.service = service
        self.planned_list = planned_list
        self.all_items: List[dict] = []
        self.seen_ids: set = set()

    @staticmethod
    def _replace_tz_with_z(iso_value: datetime | str) -> str:
        if isinstance(iso_value, datetime):
            iso_str = iso_value.replace(tzinfo=None).isoformat(timespec="milliseconds")
        else:
            iso_str = str(iso_value).strip().replace(" ", "T")
            iso_str = re.sub(r"([+-]\d{2}:\d{2}|Z)$", "", iso_str)
            if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", iso_str):
                iso_str += ".000"
        return f"{iso_str}Z"

    def _append_items(self, items: List[dict]) -> None:
        for item in items:
            tid = item.get("id")
            if tid and tid not in self.seen_ids:
                item["plannedItemList"] = self.planned_list
                self.all_items.append(item)
                self.seen_ids.add(tid)

    def fetch_dated_tasks(
        self, max_items: int, start_dt: datetime, end_dt_last: datetime
    ) -> None:
        page_token = None
        while True:
            remaining = max(1, max_items - len(self.all_items))
            resp = (
                self.service.tasks()
                .list(
                    tasklist=self.planned_list.id,
                    showCompleted=True,
                    showHidden=True,
                    showDeleted=False,
                    maxResults=min(100, remaining),
                    pageToken=page_token,
                    dueMin=TaskFetcher._replace_tz_with_z(start_dt),
                    dueMax=TaskFetcher._replace_tz_with_z(end_dt_last),
                )
                .execute()
            )
            self._append_items(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token or len(self.all_items) >= max_items:
                break

    def fetch_undated_tasks(self, max_items: int, include_undated: bool) -> None:
        if not include_undated or len(self.all_items) >= max_items:
            return
        page_token = None
        while True:
            remaining = max(1, max_items - len(self.all_items))
            resp = (
                self.service.tasks()
                .list(
                    tasklist=self.planned_list.id,
                    showCompleted=True,
                    showHidden=True,
                    showDeleted=False,
                    maxResults=min(100, remaining),
                    pageToken=page_token,
                )
                .execute()
            )
            undated = [t for t in resp.get("items", []) if "due" not in t]
            self._append_items(undated)
            page_token = resp.get("nextPageToken")
            if not page_token or len(self.all_items) >= max_items:
                break
