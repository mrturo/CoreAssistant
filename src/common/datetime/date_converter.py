# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import datetime as dt
from typing import Optional
from zoneinfo import ZoneInfo

from src.common.data.utilities import is_event, is_true
from src.common.datetime.formatting_types import EndContext, StartContext
from src.model import ItemType


class DateConverter:
    def __init__(self, timezone: Optional[str] = None) -> None:
        self._timezone = timezone

    def convert_start(
        self,
        start_rfc3339: Optional[str],
        context: Optional[StartContext] = None,
    ) -> Optional[str]:
        result: Optional[str] = "-"
        if not start_rfc3339:
            return result
        if "T" not in start_rfc3339:
            return start_rfc3339
        ctx = context or StartContext()
        try:
            aware_dt = self._parse_datetime(start_rfc3339)
            local_dt = self._to_local_timezone(aware_dt)
            if (
                not self._is_true(ctx.is_all_day)
                and self._is_true(ctx.is_today_or_tomorrow)
                and self._is_event(ctx.item_type)
            ):
                result = local_dt.timetz().isoformat(timespec="seconds")
            elif (
                self._is_true(ctx.is_all_day)
                and self._is_true(ctx.is_today_or_tomorrow)
                and self._is_event(ctx.item_type)
            ):
                result = None
            elif self._is_true(ctx.is_on_going) and self._is_event(ctx.item_type):
                result = local_dt.isoformat(timespec="seconds")[11:]
            elif self._is_true(ctx.is_all_day):
                result = local_dt.date().isoformat()
            elif not self._is_true(ctx.is_all_day) and ctx.calendar_days is not None:
                if ctx.calendar_days >= 1:
                    result = local_dt.isoformat(timespec="seconds")
                else:
                    result = local_dt.date().isoformat()
            else:
                result = local_dt.date().isoformat()
        except (ValueError, TypeError):
            result = start_rfc3339
        return result

    def convert_end(
        self,
        end_rfc3339: Optional[str],
        context: Optional[EndContext] = None,
    ) -> str:
        result = "-"
        if not end_rfc3339:
            return result
        if "T" not in end_rfc3339:
            return end_rfc3339
        ctx = context or EndContext()
        try:
            aware_dt = self._parse_datetime(end_rfc3339)
            local_dt = self._to_local_timezone(aware_dt)
            if self._is_true(ctx.is_all_day):
                result = local_dt.date().isoformat()
            elif ctx.calendar_days is not None:
                if ctx.calendar_days == 1:
                    result = local_dt.timetz().isoformat(timespec="seconds")
                elif ctx.calendar_days > 1:
                    result = local_dt.isoformat(timespec="seconds")
                else:
                    result = local_dt.date().isoformat()
            else:
                result = local_dt.date().isoformat()
        except (ValueError, TypeError):
            result = end_rfc3339
        return result

    @staticmethod
    def _parse_datetime(timestamp: str) -> dt.datetime:
        iso_str = timestamp.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(iso_str)

    def _to_local_timezone(self, aware_dt: dt.datetime) -> dt.datetime:
        target_tz = ZoneInfo(self._timezone) if self._timezone else None
        return aware_dt.astimezone(target_tz) if target_tz else aware_dt.astimezone()

    @staticmethod
    def _is_true(value: Optional[bool]) -> bool:
        return is_true(value)

    @staticmethod
    def _is_event(item_type: Optional[ItemType]) -> bool:
        return is_event(item_type)
