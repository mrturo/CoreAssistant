# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import (Iterable, List, Optional, Protocol, Sequence,
                    runtime_checkable)
from zoneinfo import ZoneInfo

from src.model.planned_item_list import PlannedItemList
from src.model.planned_item_status import PlannedItemStatus
from src.model.planned_item_type import PlannedItemType
from src.planned_item.date import human_end, human_start
from src.util.parameters import ParameterLoader

params = ParameterLoader()
tzinfo: ZoneInfo = params.get("TZINFO")
now: datetime = params.get("NOW")
today: datetime.date = params.get("TODAY")


@runtime_checkable
class ItemLike(Protocol):
    title: str
    status: Optional[PlannedItemStatus]
    start_raw: Optional[str]
    end_raw: Optional[str]
    subitems: Sequence[ItemLike]
    planned_item_list: Optional[PlannedItemList]

    def is_all_day(self) -> bool: ...
    def is_ongoing(self) -> bool: ...
    def calendar_days(self) -> int: ...
    def duration_str(self) -> Optional[str]: ...
    def time_until_start_str(self) -> str: ...
    def time_until_end_str(self) -> str: ...


@runtime_checkable
class ItemRenderer(Protocol):
    def render(self, items: Iterable[ItemLike]) -> str:
        raise NotImplementedError


@runtime_checkable
class ItemLineFormatter(Protocol):
    def format_line(self, item: ItemLike, level: int, indent_size: int) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class _DateFlags:
    is_today_or_tomorrow: bool = False
    is_before_today: bool = False
    is_today: bool = False
    is_tomorrow: bool = False


@dataclass(frozen=True)
class _StateFlags:
    is_on_going: bool = False
    is_ongoing: bool = False


@dataclass(frozen=True)
class _TimeHints:
    duration_str: Optional[str] = None
    time_until_start_str: Optional[str] = None
    time_until_end_str: Optional[str] = None


@dataclass(frozen=True)
class _Flags:
    date: _DateFlags
    state: _StateFlags
    time: _TimeHints


@dataclass(frozen=True)
class _HumanizeContext:
    item_type: Optional[PlannedItemType]
    is_all_day: bool
    calendar_days: int
    is_today_or_tomorrow: bool
    is_on_going: bool
    start_raw: Optional[str]
    end_raw: Optional[str]


@dataclass(frozen=True)
class _ItemMeta:
    item_type: Optional[PlannedItemType]
    is_all_day: bool
    calendar_days: int


@dataclass(frozen=True)
class _Timing:
    start: Optional[str]
    end: Optional[str]


@dataclass(frozen=True)
class _DetailsContext:
    meta: _ItemMeta
    timing: _Timing
    location: Optional[str]
    flags: _Flags
    planned_item_list: Optional[PlannedItemList]


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
        item_type: Optional[PlannedItemType],
        start_raw: Optional[str],
        end_raw: Optional[str],
    ) -> _Flags:
        if not start_raw:
            return _Flags(_DateFlags(), _StateFlags(), _TimeHints())

        date_flags = _DateFlags(
            is_today_or_tomorrow=self._is_today_or_tomorrow(start_raw),
            is_before_today=self._is_before_today(start_raw),
            is_today=self._is_today(start_raw),
            is_tomorrow=self._is_tomorrow(start_raw),
        )

        state_flags = _StateFlags(
            is_on_going=self._is_on_going(start_raw, end_raw) if end_raw else False,
            is_ongoing=(item_type == PlannedItemType.EVENT and item.is_ongoing()),
        )

        time_hints = _TimeHints(
            duration_str=(
                item.duration_str() if item_type == PlannedItemType.EVENT else None
            ),
            time_until_start_str=item.time_until_start_str(),
            time_until_end_str=(
                item.time_until_end_str()
                if item_type == PlannedItemType.EVENT
                else None
            ),
        )

        return _Flags(date=date_flags, state=state_flags, time=time_hints)

    @staticmethod
    def _status_str(raw_status: Optional[PlannedItemStatus]) -> Optional[str]:
        if raw_status is None:
            return None
        value = getattr(raw_status, "value", str(raw_status))
        return f"[{value}]"

    @staticmethod
    def _maybe_hide_status(
        status: Optional[str],
        item_type: Optional[PlannedItemType],
        flags: _Flags,
    ) -> str:
        if not status:
            return ""
        if item_type == PlannedItemType.TASK:
            if not (flags.date.is_today or flags.date.is_before_today):
                return ""
        elif item_type == PlannedItemType.EVENT:
            confirmed = f"[{PlannedItemStatus.CONFIRMED.value}]"
            if status == confirmed:
                return ""
        return status.strip()

    @staticmethod
    def _human_times(ctx: _HumanizeContext) -> tuple[Optional[str], Optional[str]]:
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
    def _details_list(ctx: _DetailsContext) -> list[str]:
        details: list[str] = []
        start = ctx.timing.start
        end = ctx.timing.end
        item_type = ctx.meta.item_type
        is_all_day = ctx.meta.is_all_day
        calendar_days = ctx.meta.calendar_days

        if start:
            if item_type == PlannedItemType.EVENT:
                details.append(("date: " if is_all_day else "start: ") + start)
            elif (
                item_type == PlannedItemType.TASK
                and not ctx.flags.date.is_today_or_tomorrow
            ):
                prefix = "dued: " if ctx.flags.date.is_before_today else "due: "
                details.append(prefix + start)

        if end:
            if item_type == PlannedItemType.EVENT and (
                (is_all_day and calendar_days > 1) or not is_all_day
            ):
                details.append("end: " + end)
            elif item_type == PlannedItemType.TASK:
                details.append("completed: " + end)

        if ctx.location and item_type == PlannedItemType.EVENT:
            details.append("location: " + ctx.location)

        if (
            item_type == PlannedItemType.EVENT
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
            _HumanizeContext(
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
            _DetailsContext(
                meta=_ItemMeta(
                    item_type=meta["item_type"],
                    is_all_day=meta["is_all_day"],
                    calendar_days=meta["calendar_days"],
                ),
                timing=_Timing(start=times[0], end=times[1]),
                location=meta["location"],
                flags=flags,
                planned_item_list=meta["planned_item_list"],
            )
        )
        details_str = f"({', '.join(details_items)})" if details_items else ""

        parts = [(" " * (indent_size * level)) + self.bullet]
        parts.append(title)
        if len(status) > 0:
            parts.append(status)

        if details_str:
            parts.append(details_str)
        return " ".join(parts).strip()


class TreeRenderer(ItemRenderer):
    def __init__(
        self,
        indent_step: int = 2,
        formatter: Optional[ItemLineFormatter] = None,
        newline: str = "\n",
        detect_cycles: bool = True,
    ) -> None:
        if indent_step < 0:
            raise ValueError("indent_step must be >= 0")
        if not newline:
            raise ValueError("newline must be non-empty")
        self._indent_step = indent_step
        self._formatter = formatter or TextItemLineFormatter()
        self._newline = newline
        self._detect_cycles = detect_cycles

    def render(self, items: Iterable[ItemLike]) -> str:
        lines: List[str] = []
        seen: set[int] = set()
        stack: List[tuple[ItemLike, int]] = []
        roots = list(items)
        for t in reversed(roots):
            stack.append((t, 1))
        while stack:
            item, level = stack.pop()
            if self._detect_cycles:
                obj_id = id(item)
                if obj_id in seen:
                    lines.append(
                        self._formatter.format_line(item, level, self._indent_step)
                        + "  [cycle]"
                    )
                    continue
                seen.add(obj_id)
            lines.append(self._formatter.format_line(item, level, self._indent_step))
            subitems = getattr(item, "subitems", ()) or ()
            if subitems:
                for sub in reversed(list(subitems)):
                    stack.append((sub, level + 1))
        return self._newline.join(lines)


class TextTreeRenderer(TreeRenderer):
    def __init__(self, indent_step: int = 2) -> None:
        super().__init__(indent_step=indent_step, formatter=TextItemLineFormatter())
