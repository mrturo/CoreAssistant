# pylint: disable=too-many-instance-attributes
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Dict, Final, List, Optional
from zoneinfo import ZoneInfo

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.model.core.enums import DataSource, ItemGroup, ItemStatus, ItemType
from src.model.list import ItemList
from src.model.rules import DateRules

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
    type: Optional[ItemType] = None
    title: str = UNTITLED
    notes: Optional[str] = None
    status: Optional[ItemStatus] = None
    start_raw: Optional[str] = None
    end_raw: Optional[str] = None
    updated_raw: Optional[str] = None
    parent: Optional[str] = None
    position: Optional[str] = None
    priority: Optional[int] = None
    project_id: Optional[str] = None
    section_id: Optional[str] = None
    labels: Optional[List[str]] = None
    hidden: bool = False
    deleted: bool = False
    links: List[Dict[str, Any]] = field(default_factory=list)
    assignment_info: Dict[str, Any] = field(default_factory=dict)
    subitems: List[PlannedItem] = field(default_factory=list)
    planned_item_list: Optional[ItemList] = None
    data_source: Optional[DataSource] = None
    _calculated_dates = DateRules.calculate_dates()

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
        if self.status is not None and not isinstance(self.status, ItemStatus):
            raise TypeError("status must be a Status or None")
        if self.type is None or not isinstance(self.type, ItemType):
            raise TypeError("type must be a Type")
        if self.data_source is not None and not isinstance(
            self.data_source, DataSource
        ):
            raise TypeError("data_source must be a DataSource or None")
        for name in ("start_raw", "end_raw", "updated_raw"):
            raw = getattr(self, name)
            if raw is not None:
                parsed = parse_rfc3339(
                    raw, keep_midnight_local=(self.type == ItemType.TASK)
                )
                setattr(self, name, None if parsed is None else parsed.isoformat())
        if (
            self.type == ItemType.EVENT
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
            getattr(self, attr), keep_midnight_local=(self.type == ItemType.TASK)
        )

    @property
    def start_at(self) -> Optional[datetime]:
        return self._get_dt("start_raw")

    @property
    def end_at(self) -> Optional[datetime]:
        return self._get_dt("end_raw")

    def is_root(self) -> bool:
        return self.parent is None

    def add_subitem(self, subitem: PlannedItem) -> None:
        if subitem is self:
            raise ValueError("PlannedItem cannot be its own subitem")
        if subitem not in self.subitems:
            self.subitems.append(subitem)

    def is_all_day(self) -> bool:
        if self.type == ItemType.TASK:
            return True
        if self.type != ItemType.EVENT:
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
        if self.type != ItemType.EVENT:
            raise NotImplementedError("is_ongoing() is supported just for events")
        start = self.start_at
        end = self.end_at
        return start and end and start <= now <= end and not self.is_all_day()

    def calendar_days(self) -> int:
        if self.type == ItemType.TASK:
            return 1
        if self.type != ItemType.EVENT:
            raise NotImplementedError("calendar_days() is supported just for events")
        start = self.start_at
        end = self.end_at
        return (end.date() - start.date()).days + 1

    def duration_str(self) -> Optional[str]:
        if self.type != ItemType.EVENT:
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
        if self.type not in (ItemType.EVENT, ItemType.TASK):
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
        if self.type != ItemType.EVENT:
            raise NotImplementedError("time_until_end_str() is only for events")
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
            return task_ref_dt(it) if it.type == ItemType.TASK else it.start_at

        def local_date(dt: Optional[datetime]) -> Optional[datetime.date]:
            return None if dt is None else dt.astimezone(tzinfo).date()

        def category(it: PlannedItem) -> int:
            start = it.start_at
            end = it.end_at
            start_d = local_date(start)
            category: int = 4
            if it.type == ItemType.TASK:
                if (it.status == ItemStatus.COMPLETED) or (start_d and start_d < today):
                    category = 1
                if start is None:
                    category = 2
                if start_d == today:
                    category = 3
            elif it.type == ItemType.EVENT:
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
            if it.status == ItemStatus.NEEDS_ACTION:
                return 1
            if it.status == ItemStatus.CONFIRMED:
                return 2
            if it.status == ItemStatus.TENTATIVE:
                return 3
            if it.status == ItemStatus.COMPLETED:
                return 4
            if it.status == ItemStatus.CANCELLED:
                return 5
            return 6

        def item_type(it: PlannedItem) -> int:
            if it.type == ItemType.TASK:
                return 1
            if it.type == ItemType.EVENT:
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
            s, e = DateRules.item_date_span(
                item_type=it.type, start_at=it.start_at, end_at=it.end_at
            )
            s_min = s if s_min is None or s < s_min else s_min
            e_max = e if e_max is None or e > e_max else e_max
        return s_min or today, e_max or today

    @staticmethod
    def _enabled_week_flags(wd: int) -> dict[ItemGroup, bool]:
        if wd == 4:
            return {
                ItemGroup.THIS_SUNDAY: True,
                ItemGroup.THIS_WEEKEND: False,
            }
        if wd in (5, 6):
            return {
                ItemGroup.THIS_SUNDAY: False,
                ItemGroup.THIS_WEEKEND: False,
            }
        return {
            ItemGroup.THIS_SUNDAY: False,
            ItemGroup.THIS_WEEKEND: True,
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
    ) -> Optional[ItemGroup]:
        start_d = DateRules.local_date(it.start_at)
        result: Optional[ItemGroup] = None
        if it.status == ItemStatus.COMPLETED:
            result = ItemGroup.DUED
        elif start_d is None or start_d == today:
            result = ItemGroup.TODAY
        elif start_d < today:
            result = ItemGroup.DUED
        elif start_d == today + timedelta(days=1):
            result = ItemGroup.TOMORROW
        elif (
            cd["wd"] == 4
            and enabled.get(ItemGroup.THIS_SUNDAY, False)
            and start_d == cd["this_week_sun"]
        ):
            result = ItemGroup.THIS_SUNDAY
        elif enabled.get(ItemGroup.THIS_WEEKEND, False) and DateRules.in_this_weekend(
            start_d
        ):
            result = ItemGroup.THIS_WEEKEND
        elif DateRules.in_rest_of_this_week(start_d) and DateRules.is_weekday(start_d):
            result = ItemGroup.REST_OF_THIS_WEEK
        elif DateRules.in_next_week_range(start_d):
            result = ItemGroup.NEXT_WEEK
        elif (
            start_d.month == today.month
            and start_d.year == today.year
            and start_d > cd["this_week_sun"]
        ):
            result = ItemGroup.REST_OF_THIS_MONTH
        elif (
            today.month == 12 and start_d.month == 1 and start_d.year == today.year + 1
        ) or (start_d.month == today.month + 1 and start_d.year == today.year):
            result = ItemGroup.NEXT_MONTH
        elif start_d >= cd["first_month_after_next"]:
            result = ItemGroup.FUTURE
        return result

    @staticmethod
    def _group_for_event(  # noqa: PLR0911
        it: PlannedItem,
        *,
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> Optional[ItemGroup]:
        start = it.start_at
        end = it.end_at
        start_d = DateRules.local_date(start)
        result: Optional[ItemGroup] = None
        if it.is_ongoing():
            result = ItemGroup.ON_GOING
        elif start is None and end is None:
            result = ItemGroup.TODAY
        elif (start and end and start <= now <= end) or (start_d == today):
            result = ItemGroup.TODAY
        elif start_d == today + timedelta(days=1):
            result = ItemGroup.TOMORROW
        elif (
            cd["wd"] == 4
            and enabled.get(ItemGroup.THIS_SUNDAY, False)
            and start_d == cd["this_week_sun"]
        ):
            result = ItemGroup.THIS_SUNDAY
        elif start_d:
            if enabled.get(ItemGroup.THIS_WEEKEND, False) and DateRules.in_this_weekend(
                start_d
            ):
                result = ItemGroup.THIS_WEEKEND
            elif DateRules.in_rest_of_this_week(start_d) and DateRules.is_weekday(
                start_d
            ):
                result = ItemGroup.REST_OF_THIS_WEEK
            elif DateRules.in_next_week_range(start_d):
                result = ItemGroup.NEXT_WEEK
            elif (
                start_d.month == today.month
                and start_d.year == today.year
                and start_d > cd["this_week_sun"]
            ):
                result = ItemGroup.REST_OF_THIS_MONTH
            elif (
                today.month == 12
                and start_d.month == 1
                and start_d.year == today.year + 1
            ) or (start_d.month == today.month + 1 and start_d.year == today.year):
                result = ItemGroup.NEXT_MONTH
            elif start_d >= cd["first_month_after_next"]:
                result = ItemGroup.FUTURE
        return result

    @staticmethod
    def _group_for_item(
        it: PlannedItem,
        *,
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> Optional[ItemGroup]:
        if it.type == ItemType.TASK:
            return PlannedItem._group_for_task(it, cd=cd, enabled=enabled)
        if it.type == ItemType.EVENT:
            return PlannedItem._group_for_event(it, cd=cd, enabled=enabled)
        raise NotImplementedError(f"Unknown item type: {it.type}")

    @staticmethod
    def _maybe_promote_this_friday(
        groups: dict[ItemGroup, list[PlannedItem]],
    ) -> None:
        rotw = groups.get(ItemGroup.REST_OF_THIS_WEEK, [])
        if not rotw:
            return
        cd = PlannedItem._calculated_dates
        if all(
            DateRules.is_exactly_on(
                cd["this_week_fri"], it.type, it.start_at, it.end_at
            )
            for it in rotw
        ):
            groups.setdefault(ItemGroup.THIS_FRIDAY, []).extend(rotw)
            groups[ItemGroup.REST_OF_THIS_WEEK] = []

    @staticmethod
    def _compute_enabled_flags(wd: int) -> dict[str, bool]:
        base = PlannedItem._enabled_week_flags(wd)
        base.setdefault(ItemGroup.THIS_WEEKEND, True)
        base.setdefault(ItemGroup.THIS_SUNDAY, True)
        return base

    @staticmethod
    def _distribute_into_buckets(
        items: list[PlannedItem],
        order: list[str],
        cd: dict[str, datetime.date | int],
        enabled: dict[str, bool],
    ) -> dict[ItemGroup, list[PlannedItem]]:
        buckets: dict[ItemGroup, list[PlannedItem]] = PlannedItem._init_groups(order)
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
        buckets: dict[ItemGroup, list[PlannedItem]],
    ) -> None:
        try:
            start_idx = order.index(ItemGroup.REST_OF_THIS_MONTH)
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
        buckets: dict[ItemGroup, list[PlannedItem]],
    ) -> dict[str, tuple[Period, list[PlannedItem]]]:
        result: dict[str, tuple[Period, list[PlannedItem]]] = {}
        for group in order:
            if group not in buckets:
                continue
            entries = buckets[group]
            p = DateRules.fixed_period_for(group)
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
        order = ItemGroup.ordered()
        buckets = PlannedItem._distribute_into_buckets(
            items=items, order=order, cd=cd, enabled=enabled
        )
        PlannedItem._dedupe_after_month(order=order, buckets=buckets)
        return PlannedItem._build_result(order=order, buckets=buckets)
