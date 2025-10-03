# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

from src.model.planned_item_type import PlannedItemType


@dataclass(frozen=True)
class StartContext:
    is_all_day: Optional[bool] = None
    calendar_days: Optional[int] = None
    is_today_or_tomorrow: Optional[bool] = None
    is_on_going: Optional[bool] = None
    item_type: Optional[PlannedItemType] = None


@dataclass(frozen=True)
class EndContext:
    is_all_day: Optional[bool] = None
    calendar_days: Optional[int] = None


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
        return value is True

    @staticmethod
    def _is_event(item_type: Optional[PlannedItemType]) -> bool:
        if item_type is None:
            return False
        try:
            return item_type in (PlannedItemType.EVENT, PlannedItemType.EVENT.value)
        except AttributeError:
            return False


def _start_context_from_kwargs(kwargs: Mapping[str, Any]) -> StartContext:
    return StartContext(
        is_all_day=kwargs.get("is_all_day"),
        calendar_days=kwargs.get("calendar_days"),
        is_today_or_tomorrow=kwargs.get("is_today_or_tomorrow"),
        is_on_going=kwargs.get("is_on_going"),
        item_type=kwargs.get("item_type"),
    )


def _end_context_from_kwargs(kwargs: Mapping[str, Any]) -> EndContext:
    return EndContext(
        is_all_day=kwargs.get("is_all_day"),
        calendar_days=kwargs.get("calendar_days"),
    )


def human_start(
    start_rfc3339: Optional[str],
    tz: Optional[str] = None,
    **kwargs: Any,
) -> Optional[str]:
    converter = DateConverter(tz)
    context = _start_context_from_kwargs(kwargs)
    return converter.convert_start(start_rfc3339=start_rfc3339, context=context)


def human_end(
    end_rfc3339: Optional[str],
    tz: Optional[str] = None,
    **kwargs: Any,
) -> str:
    converter = DateConverter(tz)
    context = _end_context_from_kwargs(kwargs)
    return converter.convert_end(end_rfc3339=end_rfc3339, context=context)
