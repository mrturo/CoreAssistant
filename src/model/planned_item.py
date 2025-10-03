# pylint: disable=too-many-instance-attributes
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Dict, Final, List, Optional
from zoneinfo import ZoneInfo

from src.model.planned_item_date_rules import PlannedItemDateRules
from src.model.planned_item_group import PlannedItemGroup
from src.model.planned_item_list import PlannedItemList
from src.model.planned_item_status import PlannedItemStatus
from src.model.planned_item_type import PlannedItemType
from src.util.parameters import ParameterLoader
from src.util.period import Period

params = ParameterLoader()
tzinfo: ZoneInfo = params.get("TZINFO")
now: datetime = params.get("NOW")
today: datetime.date = params.get("TODAY")
UNTITLED: Final[str] = "(untitled)"


def parse_rfc3339(
    value: Optional[str], *, keep_midnight_local: bool = False
) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid RFC3339 datetime: {value!r}") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzinfo)
        if keep_midnight_local and dt.time() == time(0, 0, 0):
            return dt
        return dt.astimezone(tzinfo)
    if keep_midnight_local and dt.time() == time(0, 0, 0):
        return datetime.combine(dt.date(), time(0, 0, 0), tzinfo=tzinfo)
    return dt.astimezone(tzinfo)


def format_rfc3339(value: Optional[datetime]) -> Optional[str]:
    if not value:
        return None
    if value.tzinfo is None:
        raise ValueError("Expected timezone-aware datetime")
    return value.isoformat(timespec="seconds")


def _clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


@dataclass
class PlannedItem:
    kind: Optional[str] = None
    id: Optional[str] = None
    etag: Optional[str] = None
    self_link: Optional[str] = None
    web_view_link: Optional[str] = None
    type: Optional[PlannedItemType] = None
    title: str = UNTITLED
    notes: Optional[str] = None
    status: Optional[PlannedItemStatus] = None
    start_raw: Optional[str] = None
    end_raw: Optional[str] = None
    updated_raw: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    hidden: bool = False
    deleted: bool = False
    links: List[Dict[str, Any]] = field(default_factory=list)
    assignment_info: Dict[str, Any] = field(default_factory=dict)
    subitems: List[PlannedItem] = field(default_factory=list)
    planned_item_list: Optional[PlannedItemList] = None

    _calculated_dates = PlannedItemDateRules.calculate_dates()

    def __post_init__(self) -> None:
        self.kind = _clean_str(self.kind)
        self.id = _clean_str(self.id)
        self.etag = _clean_str(self.etag)
        self.self_link = _clean_str(self.self_link)
        self.web_view_link = _clean_str(self.web_view_link)
        self.title = (self.title or UNTITLED).strip() or UNTITLED
        self.notes = _clean_str(self.notes)
        self.parent = _clean_str(self.parent)
        self.position = _clean_str(self.position)
        if self.status is not None and not isinstance(self.status, PlannedItemStatus):
            raise TypeError("status must be a Status or None")
        if self.type is None or not isinstance(self.type, PlannedItemType):
            raise TypeError("type must be a Type")
        for name in ("start_raw", "end_raw", "updated_raw"):
            raw = getattr(self, name)
            if raw is not None:
                parsed = parse_rfc3339(
                    raw, keep_midnight_local=(self.type == PlannedItemType.TASK)
                )
                setattr(self, name, None if parsed is None else parsed.isoformat())
        if (
            self.type == PlannedItemType.EVENT
            and self.start_raw is not None
            and self.end_raw is not None
        ):
            dt = datetime.fromisoformat(self.end_raw)
            if dt.time() == datetime.min.time():
                dt = dt - timedelta(seconds=1)
                self.end_raw = dt.isoformat()
        for st in self.subitems:
            if st is self:
                raise ValueError("PlannedItem cannot be its own subitem")

    def _get_dt(self, attr: str) -> Optional[datetime]:
        return parse_rfc3339(
            getattr(self, attr), keep_midnight_local=(self.type == PlannedItemType.TASK)
        )

    @property
    def start_at(self) -> Optional[datetime]:
        return self._get_dt("start_raw")

    @property
    def end_at(self) -> Optional[datetime]:
        return self._get_dt("end_raw")

    @property
    def updated_at(self) -> Optional[datetime]:
        return self._get_dt("updated_raw")

    def is_root(self) -> bool:
        return self.parent is None

    def is_completed(self) -> bool:
        if self.type == PlannedItemType.EVENT:
            return self.end_raw <= now
        if self.type == PlannedItemType.TASK:
            return self.status == PlannedItemStatus.COMPLETED
        raise NotImplementedError("is_completed() is supported just for task and event")

    def is_pending(self) -> bool:
        if self.type == PlannedItemType.EVENT:
            return self.end_raw > now
        if self.type == PlannedItemType.TASK:
            return self.status == PlannedItemStatus.NEEDS_ACTION
        raise NotImplementedError("is_pending() is supported just for task and event")

    def is_all_day(self) -> bool:
        if self.type == PlannedItemType.TASK:
            return True
        if self.type != PlannedItemType.EVENT:
            raise NotImplementedError("is_all_day() is supported just for events")
        start = self.start_at
        end = self.end_at
        if not start or not end:
            return False
        start_time = start.time()
        end_time = end.time()
        duration = end - start
        if (
            start_time == time(0, 0, 0)
            and end_time == time(23, 59, 59)
            and duration.total_seconds() % 86400 == 86399
        ):
            return True
        return False

    def is_ongoing(self) -> bool:
        if self.type != PlannedItemType.EVENT:
            raise NotImplementedError("is_ongoing() is supported just for events")
        start = self.start_at
        end = self.end_at
        return start and end and start <= now <= end and not self.is_all_day()

    def calendar_days(self) -> int:
        if self.type == PlannedItemType.TASK:
            return 1
        if self.type != PlannedItemType.EVENT:
            raise NotImplementedError("calendar_days() is supported just for events")
        start = self.start_at
        end = self.end_at
        return (end.date() - start.date()).days + 1

    def duration_str(self) -> Optional[str]:
        if self.type != PlannedItemType.EVENT:
            raise NotImplementedError("duration_str() is supported just for events")
        start = self.start_at
        end = self.end_at
        if not start or not end:
            return None
        delta: timedelta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds % 60 == 59:
            total_seconds += 1
        if total_seconds < 0:
            return None
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        return "".join(parts) if parts else "0m"

    def time_until_start_str(self) -> str:
        if self.type not in (PlannedItemType.EVENT, PlannedItemType.TASK):
            raise NotImplementedError(
                "time_until_start_str() is supported just for events and tasks"
            )
        start = self.start_at
        if not start:
            return None
        delta: timedelta = start - now
        total_seconds = int(delta.total_seconds())
        if total_seconds % 60 == 59:
            total_seconds += 1
        if total_seconds <= 0:
            return None
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        if days > 0:
            return f"{days+1}d"
        parts: list[str] = []
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return "".join(parts)

    def time_until_end_str(self) -> str:
        if self.type != PlannedItemType.EVENT:
            raise NotImplementedError("time_until_end_str() es solo para eventos")
        start = self.start_at
        end = self.end_at
        if not end or not start:
            return None
        if not start <= now < end:
            return None
        delta: timedelta = end - now
        total_seconds = int(delta.total_seconds())
        if total_seconds % 60 == 59:
            total_seconds += 1
        if total_seconds <= 0:
            return None
        days, rem = divmod(total_seconds, 86400)
        if days > 0:
            return f"{days}d"
        hours, rem = divmod(rem, 3600)
        minutes = rem // 60
        parts: list[str] = []
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return "".join(parts)

    def __str__(self) -> str:
        return f"PlannedItem({asdict(self)!r})"

    @staticmethod
    def sort(items: List[PlannedItem]) -> List[PlannedItem]:
        def task_ref_dt(it: PlannedItem) -> Optional[datetime]:
            return it.start_at or it.end_at

        def effective_start(it: PlannedItem) -> Optional[datetime]:
            return task_ref_dt(it) if it.type == PlannedItemType.TASK else it.start_at

        def local_date(dt: Optional[datetime]) -> Optional[datetime.date]:
            return None if dt is None else dt.astimezone(tzinfo).date()

        def category(it: PlannedItem) -> int:
            start = it.start_at
            end = it.end_at
            start_d = local_date(start)
            category: int = 4
            if it.type == PlannedItemType.TASK:
                if (it.status == PlannedItemStatus.COMPLETED) or (
                    start_d and start_d < today
                ):
                    category = 1
                if start is None:
                    category = 2
                if start_d == today:
                    category = 3
            elif it.type == PlannedItemType.EVENT:
                if (end and end < now) or (start and start < now):
                    category = 1
                if start is None and end is None:
                    category = 2
                if (start and end and start <= now <= end) or (start_d == today):
                    category = 3
            else:
                raise NotImplementedError(f"Unknown item type: {it.type}")
            return category

        def status(it: PlannedItem) -> int:
            if it.status == PlannedItemStatus.NEEDS_ACTION:
                return 1
            if it.status == PlannedItemStatus.CONFIRMED:
                return 2
            if it.status == PlannedItemStatus.TENTATIVE:
                return 3
            if it.status == PlannedItemStatus.COMPLETED:
                return 4
            if it.status == PlannedItemStatus.CANCELLED:
                return 5
            return 6

        def item_type(it: PlannedItem) -> int:
            if it.type == PlannedItemType.TASK:
                return 1
            if it.type == PlannedItemType.EVENT:
                return 2
            return 3

        def title_key(it: PlannedItem) -> str:
            return (it.title or UNTITLED).strip().casefold()

        def keyfn(it: PlannedItem) -> tuple:
            cat = category(it)
            sta = status(it)
            typ = item_type(it)
            ref = effective_start(it)
            tkey = title_key(it)
            if cat == 2 or ref is None:
                return (cat, sta, typ, tkey)
            return (cat, ref.astimezone(tzinfo), sta, typ, tkey)

        return sorted(items, key=keyfn)

    @staticmethod
    def dynamic_span(
        entries: list[PlannedItem],
    ) -> tuple[datetime.date, datetime.date]:
        if not entries:
            return today, today
        s_min: Optional[datetime.date] = None
        e_max: Optional[datetime.date] = None
        for it in entries:
            s, e = PlannedItemDateRules.item_date_span(
                item_type=it.type, start_at=it.start_at, end_at=it.end_at
            )
            s_min = s if s_min is None or s < s_min else s_min
            e_max = e if e_max is None or e > e_max else e_max
        return s_min or today, e_max or today

    @staticmethod
    def _enabled_week_flags(wd: int) -> dict[PlannedItemGroup, bool]:
        if wd == 4:
            return {
                PlannedItemGroup.THIS_SUNDAY: True,
                PlannedItemGroup.THIS_WEEKEND: False,
            }
        if wd in (5, 6):
            return {
                PlannedItemGroup.THIS_SUNDAY: False,
                PlannedItemGroup.THIS_WEEKEND: False,
            }
        return {
            PlannedItemGroup.THIS_SUNDAY: False,
            PlannedItemGroup.THIS_WEEKEND: True,
        }

    @staticmethod
    def _init_groups(groups: list[str]) -> dict[str, list[PlannedItem]]:
        return {g: [] for g in groups}

    @staticmethod
    def _group_for_task(  # noqa: PLR0911
        it: PlannedItem,
        *,
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> Optional[PlannedItemGroup]:
        start_d = PlannedItemDateRules.local_date(it.start_at)
        result: Optional[PlannedItemGroup] = None
        if it.status == PlannedItemStatus.COMPLETED:
            result = PlannedItemGroup.DUED
        elif start_d is None or start_d == today:
            result = PlannedItemGroup.TODAY
        elif start_d < today:
            result = PlannedItemGroup.DUED
        elif start_d == today + timedelta(days=1):
            result = PlannedItemGroup.TOMORROW
        elif (
            cd["wd"] == 4
            and enabled.get(PlannedItemGroup.THIS_SUNDAY, False)
            and start_d == cd["this_week_sun"]
        ):
            result = PlannedItemGroup.THIS_SUNDAY
        elif enabled.get(
            PlannedItemGroup.THIS_WEEKEND, False
        ) and PlannedItemDateRules.in_this_weekend(start_d):
            result = PlannedItemGroup.THIS_WEEKEND
        elif PlannedItemDateRules.in_rest_of_this_week(
            start_d
        ) and PlannedItemDateRules.is_weekday(start_d):
            result = PlannedItemGroup.REST_OF_THIS_WEEK
        elif PlannedItemDateRules.in_next_week_range(start_d):
            result = PlannedItemGroup.NEXT_WEEK
        elif (
            start_d.month == today.month
            and start_d.year == today.year
            and start_d > cd["this_week_sun"]
        ):
            result = PlannedItemGroup.REST_OF_THIS_MONTH
        elif (
            today.month == 12 and start_d.month == 1 and start_d.year == today.year + 1
        ) or (start_d.month == today.month + 1 and start_d.year == today.year):
            result = PlannedItemGroup.NEXT_MONTH
        elif start_d >= cd["first_month_after_next"]:
            result = PlannedItemGroup.FUTURE
        return result

    @staticmethod
    def _group_for_event(  # noqa: PLR0911
        it: PlannedItem,
        *,
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> Optional[PlannedItemGroup]:
        start = it.start_at
        end = it.end_at
        start_d = PlannedItemDateRules.local_date(start)

        result: Optional[PlannedItemGroup] = None
        if it.is_ongoing():
            result = PlannedItemGroup.ON_GOING
        elif start is None and end is None:
            result = PlannedItemGroup.TODAY
        elif (start and end and start <= now <= end) or (start_d == today):
            result = PlannedItemGroup.TODAY
        elif start_d == today + timedelta(days=1):
            result = PlannedItemGroup.TOMORROW
        elif (
            cd["wd"] == 4
            and enabled.get(PlannedItemGroup.THIS_SUNDAY, False)
            and start_d == cd["this_week_sun"]
        ):
            result = PlannedItemGroup.THIS_SUNDAY
        elif start_d:
            if enabled.get(
                PlannedItemGroup.THIS_WEEKEND, False
            ) and PlannedItemDateRules.in_this_weekend(start_d):
                result = PlannedItemGroup.THIS_WEEKEND
            elif PlannedItemDateRules.in_rest_of_this_week(
                start_d
            ) and PlannedItemDateRules.is_weekday(start_d):
                result = PlannedItemGroup.REST_OF_THIS_WEEK
            elif PlannedItemDateRules.in_next_week_range(start_d):
                result = PlannedItemGroup.NEXT_WEEK
            elif (
                start_d.month == today.month
                and start_d.year == today.year
                and start_d > cd["this_week_sun"]
            ):
                result = PlannedItemGroup.REST_OF_THIS_MONTH
            elif (
                today.month == 12
                and start_d.month == 1
                and start_d.year == today.year + 1
            ) or (start_d.month == today.month + 1 and start_d.year == today.year):
                result = PlannedItemGroup.NEXT_MONTH
            elif start_d >= cd["first_month_after_next"]:
                result = PlannedItemGroup.FUTURE
        return result

    @staticmethod
    def _group_for_item(
        it: PlannedItem,
        *,
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> Optional[PlannedItemGroup]:
        if it.type == PlannedItemType.TASK:
            return PlannedItem._group_for_task(it, cd=cd, enabled=enabled)
        if it.type == PlannedItemType.EVENT:
            return PlannedItem._group_for_event(it, cd=cd, enabled=enabled)
        raise NotImplementedError(f"Unknown item type: {it.type}")

    @staticmethod
    def _maybe_promote_this_friday(
        groups: dict[PlannedItemGroup, list[PlannedItem]],
    ) -> None:
        rotw = groups.get(PlannedItemGroup.REST_OF_THIS_WEEK, [])
        if not rotw:
            return
        cd = PlannedItem._calculated_dates
        if all(
            PlannedItemDateRules.is_exactly_on(
                cd["this_week_fri"], it.type, it.start_at, it.end_at
            )
            for it in rotw
        ):
            groups.setdefault(PlannedItemGroup.THIS_FRIDAY, []).extend(rotw)
            groups[PlannedItemGroup.REST_OF_THIS_WEEK] = []

    @staticmethod
    def _compute_enabled_flags(wd: int) -> dict[str, bool]:
        base = PlannedItem._enabled_week_flags(wd)
        base.setdefault(PlannedItemGroup.THIS_WEEKEND, True)
        base.setdefault(PlannedItemGroup.THIS_SUNDAY, True)
        return base

    @staticmethod
    def _distribute_into_buckets(
        items: list[PlannedItem],
        order: list[str],
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> dict[PlannedItemGroup, list[PlannedItem]]:
        buckets: dict[PlannedItemGroup, list[PlannedItem]] = PlannedItem._init_groups(
            order
        )
        for it in items:
            group = PlannedItem._group_for_item(it, cd=cd, enabled=enabled)
            if group is None:
                continue
            buckets.setdefault(group, []).append(it)

        PlannedItem._maybe_promote_this_friday(buckets)
        return buckets

    @staticmethod
    def _dedupe_after_month(
        order: list[str],
        buckets: dict[PlannedItemGroup, list[PlannedItem]],
    ) -> None:
        try:
            start_idx = order.index(PlannedItemGroup.REST_OF_THIS_MONTH)
        except ValueError:
            return

        seen_titles: set[str] = set()
        for g in order[:start_idx]:
            for _it in buckets.get(g, []):
                seen_titles.add((_it.title or "").strip())

        for g in order[start_idx:]:
            if g not in buckets:
                continue
            filtered: list[PlannedItem] = []
            for _it in buckets[g]:
                key = (_it.title or "").strip()
                if key and key not in seen_titles:
                    filtered.append(_it)
                    seen_titles.add(key)
            buckets[g] = filtered

    @staticmethod
    def _build_result(
        order: list[str],
        buckets: dict[PlannedItemGroup, list[PlannedItem]],
    ) -> dict[str, tuple[Period, list[PlannedItem]]]:
        result: dict[str, tuple[Period, list[PlannedItem]]] = {}
        for group in order:
            if group not in buckets:
                continue
            entries = buckets[group]
            p = PlannedItemDateRules.fixed_period_for(group)
            if p is None:
                s, e = PlannedItem.dynamic_span(entries)
                p = Period(start=s, end=e, inclusive=True, duration=(e - s).days + 1)
            result[group] = (p, entries)
        return result

    @staticmethod
    def time_grouper(
        items: list[PlannedItem],
    ) -> dict[str, tuple[Period, list[PlannedItem]]]:
        cd = PlannedItem._calculated_dates
        enabled = PlannedItem._compute_enabled_flags(cd["wd"])
        order = PlannedItemGroup.ordered()

        buckets = PlannedItem._distribute_into_buckets(
            items=items, order=order, cd=cd, enabled=enabled
        )
        PlannedItem._dedupe_after_month(order=order, buckets=buckets)
        return PlannedItem._build_result(order=order, buckets=buckets)
