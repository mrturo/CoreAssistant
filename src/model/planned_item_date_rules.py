# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

from datetime import date, datetime, timedelta
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from src.model.planned_item_group import PlannedItemGroup
from src.model.planned_item_type import PlannedItemType
from src.util.parameters import ParameterLoader
from src.util.period import Period


class PlannedItemDateRules:

    _params = ParameterLoader()
    _tzinfo: ZoneInfo = _params.get("TZINFO")
    _today: datetime.date = _params.get("TODAY")

    @staticmethod
    def _first_day(year: int, month: int) -> datetime.date:
        return datetime(year, month, 1, tzinfo=PlannedItemDateRules._tzinfo).date()

    @staticmethod
    def _next_month(d: datetime.date) -> tuple[int, int]:
        m = 1 if d.month == 12 else d.month + 1
        y = d.year + 1 if d.month == 12 else d.year
        return y, m

    @staticmethod
    def _month_after_next(d: datetime.date) -> tuple[int, int]:
        y1, m1 = PlannedItemDateRules._next_month(d)
        y2, m2 = (y1 + (1 if m1 == 12 else 0), 1 if m1 == 12 else m1 + 1)
        return y2, m2

    @staticmethod
    def local_date(dt: Optional[datetime]) -> Optional[datetime.date]:
        return (
            None if dt is None else dt.astimezone(PlannedItemDateRules._tzinfo).date()
        )

    @staticmethod
    def item_date_span(
        item_type: Optional[PlannedItemType],
        start_at: Optional[datetime],
        end_at: Optional[datetime],
    ) -> tuple[datetime.date, datetime.date]:
        if item_type == PlannedItemType.TASK:
            ref = start_at or end_at
            d = PlannedItemDateRules.local_date(ref) or PlannedItemDateRules._today
            return d, d
        if item_type == PlannedItemType.EVENT:
            s = PlannedItemDateRules.local_date(start_at)
            e = PlannedItemDateRules.local_date(end_at)
            if s is None and e is None:
                return PlannedItemDateRules._today, PlannedItemDateRules._today
            if s is None:
                return e, e
            if e is None:
                return s, s
            return s, e
        raise NotImplementedError(f"Unknown item type: {item_type}")

    @staticmethod
    def is_weekday(d: datetime.date) -> bool:
        return d.weekday() <= 4

    @staticmethod
    def in_rest_of_this_week(d: datetime.date) -> bool:
        start = max(
            PlannedItemDateRules._today + timedelta(days=2), PlannedItemDateRules._today
        )
        end = PlannedItemDateRules.calculate_dates()["this_week_fri"]
        return start <= d <= end

    @staticmethod
    def in_this_weekend(d: datetime.date) -> bool:
        return (
            PlannedItemDateRules.calculate_dates()["this_week_sat"]
            <= d
            <= PlannedItemDateRules.calculate_dates()["this_week_sun"]
        )

    @staticmethod
    def in_next_week_range(d: datetime.date) -> bool:
        if PlannedItemDateRules.calculate_dates()["wd"] == 6:
            return (
                PlannedItemDateRules.calculate_dates()["next_week_tue"]
                <= d
                <= PlannedItemDateRules.calculate_dates()["next_week_sun"]
            )
        return (
            PlannedItemDateRules.calculate_dates()["next_week_mon"]
            <= d
            <= PlannedItemDateRules.calculate_dates()["next_week_sun"]
        )

    @staticmethod
    def is_exactly_on(
        d: datetime.date,
        item_type: Optional[PlannedItemType],
        start_at: Optional[datetime],
        end_at: Optional[datetime],
    ) -> bool:
        s, e = PlannedItemDateRules.item_date_span(item_type, start_at, end_at)
        return s == d and e == d

    @staticmethod
    def fixed_period_for(group: PlannedItemGroup) -> Optional[Period]:
        result: Optional[Period] = None
        if group == PlannedItemGroup.TODAY:
            result = Period(
                start=PlannedItemDateRules._today,
                end=PlannedItemDateRules._today,
                inclusive=True,
                duration=1,
            )
        elif group == PlannedItemGroup.TOMORROW:
            d = PlannedItemDateRules._today + timedelta(days=1)
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == PlannedItemGroup.REST_OF_THIS_WEEK:
            w_start = max(
                PlannedItemDateRules._today + timedelta(days=2),
                PlannedItemDateRules._today,
            )
            w_end = PlannedItemDateRules.calculate_dates()["this_week_fri"]
            w_start = min(w_start, w_end)
            result = Period(
                start=w_start,
                end=w_end,
                inclusive=True,
                duration=(w_end - w_start).days + 1,
            )
        elif group == PlannedItemGroup.THIS_FRIDAY:
            d = PlannedItemDateRules.calculate_dates()["this_week_fri"]
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == PlannedItemGroup.THIS_WEEKEND:
            ws, we = (
                PlannedItemDateRules.calculate_dates()["this_week_sat"],
                PlannedItemDateRules.calculate_dates()["this_week_sun"],
            )
            result = Period(
                start=ws, end=we, inclusive=True, duration=(we - ws).days + 1
            )
        elif group == PlannedItemGroup.THIS_SUNDAY:
            d = PlannedItemDateRules.calculate_dates()["this_week_sun"]
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == PlannedItemGroup.NEXT_WEEK:
            start = (
                PlannedItemDateRules.calculate_dates()["next_week_tue"]
                if PlannedItemDateRules.calculate_dates()["wd"] == 6
                else PlannedItemDateRules.calculate_dates()["next_week_mon"]
            )
            end = PlannedItemDateRules.calculate_dates()["next_week_sun"]
            start = min(start, end)
            result = Period(
                start=start,
                end=end,
                inclusive=True,
                duration=(end - start).days + 1,
            )
        elif group == PlannedItemGroup.REST_OF_THIS_MONTH:
            m_start = max(
                PlannedItemDateRules.calculate_dates()["this_week_sun"]
                + timedelta(days=1),
                PlannedItemDateRules.calculate_dates()["first_this_month"],
            )
            m_end = PlannedItemDateRules.calculate_dates()["last_this_month"]
            m_start = min(m_start, m_end)
            result = Period(
                start=m_start,
                end=m_end,
                inclusive=True,
                duration=(m_end - m_start).days + 1,
            )
        elif group == PlannedItemGroup.NEXT_MONTH:
            result = Period(
                start=PlannedItemDateRules.calculate_dates()["first_next_month"],
                end=PlannedItemDateRules.calculate_dates()["last_next_month"],
                inclusive=True,
                duration=(
                    PlannedItemDateRules.calculate_dates()["last_next_month"]
                    - PlannedItemDateRules.calculate_dates()["first_next_month"]
                ).days
                + 1,
            )
        return result

    @staticmethod
    def calculate_dates() -> Dict[str, date]:
        wd = PlannedItemDateRules._today.weekday()
        y_man, m_man = PlannedItemDateRules._month_after_next(
            PlannedItemDateRules._today
        )
        y_next, m_next = PlannedItemDateRules._next_month(PlannedItemDateRules._today)
        this_week_sun = PlannedItemDateRules._today + timedelta(days=6 - wd)
        next_week_mon = this_week_sun + timedelta(days=1)
        first_next_month = PlannedItemDateRules._first_day(y_next, m_next)
        first_month_after_next = PlannedItemDateRules._first_day(y_man, m_man)
        return {
            "wd": wd,
            "this_week_fri": PlannedItemDateRules._today + timedelta(days=4 - wd),
            "this_week_sat": PlannedItemDateRules._today + timedelta(days=5 - wd),
            "this_week_sun": this_week_sun,
            "next_week_mon": next_week_mon,
            "next_week_tue": next_week_mon + timedelta(days=1),
            "next_week_sun": next_week_mon + timedelta(days=6),
            "first_this_month": PlannedItemDateRules._first_day(
                PlannedItemDateRules._today.year, PlannedItemDateRules._today.month
            ),
            "first_next_month": first_next_month,
            "last_this_month": first_next_month - timedelta(days=1),
            "first_month_after_next": first_month_after_next,
            "last_next_month": first_month_after_next - timedelta(days=1),
        }
