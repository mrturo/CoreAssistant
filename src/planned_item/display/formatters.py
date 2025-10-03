# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from src.common.data.parameters import ParameterLoader
from src.common.datetime.formatting_types import (DateFlags, DetailsContext,
                                                  FormattingFlags,
                                                  HumanizeContext, ItemMeta,
                                                  StateFlags, TimeHints,
                                                  Timing)
from src.model import ItemStatus, ItemType
from src.model.protocols import ItemLike
from src.planned_item.display.date_formatting import human_end, human_start

params = ParameterLoader()
tzinfo: ZoneInfo = params.get("TZINFO")
now: datetime = params.get("NOW")
today: datetime.date = params.get("TODAY")


@dataclass
class TextItemLineFormatter:
    bullet: str = "-"

    @staticmethod
    def _parse_rfc3339(dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            normalized = dt_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo)
        return dt

    @staticmethod
    def _is_before_today(dt_str: Optional[str]) -> bool:
        dt = TextItemLineFormatter._parse_rfc3339(dt_str)
        return bool(dt and dt.astimezone(tzinfo).date() < today)

    @staticmethod
    def _is_today(dt_str: Optional[str]) -> bool:
        dt = TextItemLineFormatter._parse_rfc3339(dt_str)
        return bool(dt and dt.astimezone(tzinfo).date() == today)

    @staticmethod
    def _is_tomorrow(dt_str: Optional[str]) -> bool:
        dt = TextItemLineFormatter._parse_rfc3339(dt_str)
        return bool(dt and dt.astimezone(tzinfo).date() == today + timedelta(days=1))

    @staticmethod
    def _is_today_or_tomorrow(dt_str: Optional[str]) -> bool:
        dt = TextItemLineFormatter._parse_rfc3339(dt_str)
        if not dt:
            return False
        d = dt.astimezone(tzinfo).date()
        return d in (today, today + timedelta(days=1))

    @staticmethod
    def _is_on_going(start_str: Optional[str], end_str: Optional[str]) -> bool:
        start = TextItemLineFormatter._parse_rfc3339(start_str)
        end = TextItemLineFormatter._parse_rfc3339(end_str)
        return bool(start and end and start <= now <= end)

    @staticmethod
    def _clean_str(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        s = value.strip()
        return s if s else None

    def _build_flags(
        self,
        item: ItemLike,
        item_type: Optional[ItemType],
        start_raw: Optional[str],
        end_raw: Optional[str],
    ) -> FormattingFlags:
        if not start_raw:
            return FormattingFlags(DateFlags(), StateFlags(), TimeHints())
        date_flags = DateFlags(
            is_today_or_tomorrow=self._is_today_or_tomorrow(start_raw),
            is_before_today=self._is_before_today(start_raw),
            is_today=self._is_today(start_raw),
            is_tomorrow=self._is_tomorrow(start_raw),
        )
        state_flags = StateFlags(
            is_on_going=self._is_on_going(start_raw, end_raw) if end_raw else False,
            is_ongoing=(item_type == ItemType.EVENT and item.is_ongoing()),
        )
        time_hints = TimeHints(
            duration_str=(item.duration_str() if item_type == ItemType.EVENT else None),
            time_until_start_str=item.time_until_start_str(),
            time_until_end_str=(
                item.time_until_end_str() if item_type == ItemType.EVENT else None
            ),
        )
        return FormattingFlags(date=date_flags, state=state_flags, time=time_hints)

    @staticmethod
    def _status_str(raw_status: Optional[ItemStatus]) -> Optional[str]:
        if raw_status is None:
            return None
        value = getattr(raw_status, "value", str(raw_status))
        return f"[{value}]"

    @staticmethod
    def _maybe_hide_status(
        status: Optional[str],
        item_type: Optional[ItemType],
        flags: FormattingFlags,
    ) -> str:
        if not status:
            return ""
        if item_type == ItemType.TASK:
            if not (flags.date.is_today or flags.date.is_before_today):
                return ""
        elif item_type == ItemType.EVENT:
            confirmed = f"[{ItemStatus.CONFIRMED.value}]"
            if status == confirmed:
                return ""
        return status.strip()

    @staticmethod
    def _human_times(ctx: HumanizeContext) -> tuple[Optional[str], Optional[str]]:
        start = human_start(
            start_rfc3339=ctx.start_raw,
            is_all_day=ctx.is_all_day,
            calendar_days=ctx.calendar_days,
            is_today_or_tomorrow=ctx.is_today_or_tomorrow,
            is_on_going=ctx.is_on_going,
            item_type=ctx.item_type,
        )
        end = human_end(
            end_rfc3339=ctx.end_raw,
            is_all_day=ctx.is_all_day,
            calendar_days=ctx.calendar_days,
        )
        return (None if start == "-" else start, None if end == "-" else end)

    @staticmethod
    def _details_list(ctx: DetailsContext) -> list[str]:
        details: list[str] = []
        start = ctx.timing.start
        end = ctx.timing.end
        item_type = ctx.meta.item_type
        is_all_day = ctx.meta.is_all_day
        calendar_days = ctx.meta.calendar_days
        if start:
            if item_type == ItemType.EVENT:
                details.append(("date: " if is_all_day else "start: ") + start)
            elif item_type == ItemType.TASK and not ctx.flags.date.is_today_or_tomorrow:
                prefix = "dued: " if ctx.flags.date.is_before_today else "due: "
                details.append(prefix + start)
        if end:
            if item_type == ItemType.EVENT and (
                (is_all_day and calendar_days > 1) or not is_all_day
            ):
                details.append("end: " + end)
            elif item_type == ItemType.TASK:
                details.append("completed: " + end)
        if ctx.location and item_type == ItemType.EVENT:
            details.append("location: " + ctx.location)
        if (
            item_type == ItemType.EVENT
            and ctx.flags.time.duration_str is not None
            and ctx.flags.time.duration_str != "1d"
        ):
            details.append("duration: " + ctx.flags.time.duration_str)
        if ctx.flags.time.time_until_start_str and not ctx.flags.date.is_tomorrow:
            details.append("in: " + ctx.flags.time.time_until_start_str)
        if ctx.flags.time.time_until_end_str and ctx.flags.state.is_ongoing:
            details.append("until: " + ctx.flags.time.time_until_end_str)
        if ctx.planned_item_list:
            details.append("list: " + ctx.planned_item_list.name)
        if ctx.data_source:
            details.append("source: " + ctx.data_source.value)
        return details

    def format_line(self, item: ItemLike, level: int, indent_size: int) -> str:
        title = getattr(item, "title", None)
        if title is not None and not isinstance(title, str):
            raise ValueError("Item title must be a string.")
        if title is None:
            raise ValueError("Item title is missing.")
        if len(title.strip()) == 0:
            raise ValueError("Item title must not be empty or whitespace.")
        title = title.strip()
        start_raw = self._clean_str(getattr(item, "start_raw", None))
        end_raw = self._clean_str(getattr(item, "end_raw", None))
        meta = {
            "item_type": getattr(item, "type", None),
            "location": self._clean_str(getattr(item, "location", None)),
            "is_all_day": item.is_all_day(),
            "calendar_days": item.calendar_days(),
            "planned_item_list": getattr(item, "planned_item_list", None),
        }
        flags = self._build_flags(item, meta["item_type"], start_raw, end_raw)
        status = self._maybe_hide_status(
            self._status_str(getattr(item, "status", None)), meta["item_type"], flags
        )
        times = self._human_times(
            HumanizeContext(
                item_type=meta["item_type"],
                is_all_day=meta["is_all_day"],
                calendar_days=meta["calendar_days"],
                is_today_or_tomorrow=flags.date.is_today_or_tomorrow,
                is_on_going=flags.state.is_on_going,
                start_raw=start_raw,
                end_raw=end_raw,
            )
        )
        details_items = self._details_list(
            DetailsContext(
                meta=ItemMeta(
                    item_type=meta["item_type"],
                    is_all_day=meta["is_all_day"],
                    calendar_days=meta["calendar_days"],
                ),
                timing=Timing(start=times[0], end=times[1]),
                location=meta["location"],
                flags=flags,
                planned_item_list=meta["planned_item_list"],
                data_source=getattr(item, "data_source", None),
            )
        )
        details_str = f"({', '.join(details_items)})" if details_items else ""
        parts = [(" " * (indent_size * level)) + self.bullet]
        parts.append(title)
        if len(status) > 0:
            parts.append(status)
        if details_str:
            parts.append(details_str)
        return " ".join(parts).rstrip()


__all__ = ["TextItemLineFormatter"]
