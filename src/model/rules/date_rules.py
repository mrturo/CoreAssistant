# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from datetime import date, datetime, timedelta
from typing import Dict, Optional
from zoneinfo import ZoneInfo

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.model.core.enums import ItemGroup, ItemType


class DateRules:
    _params = ParameterLoader()
    _tzinfo: ZoneInfo = _params.get("TZINFO")
    _today: datetime.date = _params.get("TODAY")

    @staticmethod
    def _first_day(year: int, month: int) -> datetime.date:
        return datetime(year, month, 1, tzinfo=DateRules._tzinfo).date()

    @staticmethod
    def _next_month(d: datetime.date) -> tuple[int, int]:
        m = 1 if d.month == 12 else d.month + 1
        y = d.year + 1 if d.month == 12 else d.year
        return y, m

    @staticmethod
    def _month_after_next(d: datetime.date) -> tuple[int, int]:
        y1, m1 = DateRules._next_month(d)
        y2, m2 = (y1 + (1 if m1 == 12 else 0), 1 if m1 == 12 else m1 + 1)
        return y2, m2

    @staticmethod
    def local_date(dt: Optional[datetime]) -> Optional[datetime.date]:
        return None if dt is None else dt.astimezone(DateRules._tzinfo).date()

    @staticmethod
    def item_date_span(
        item_type: Optional[ItemType],
        start_at: Optional[datetime],
        end_at: Optional[datetime],
    ) -> tuple[datetime.date, datetime.date]:
        if item_type == ItemType.TASK:
            ref = start_at or end_at
            d = DateRules.local_date(ref) or DateRules._today
            return d, d
        if item_type == ItemType.EVENT:
            s = DateRules.local_date(start_at)
            e = DateRules.local_date(end_at)
            if s is None and e is None:
                return DateRules._today, DateRules._today
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
        start = max(DateRules._today + timedelta(days=2), DateRules._today)
        end = DateRules.calculate_dates()["this_week_fri"]
        return start <= d <= end

    @staticmethod
    def in_this_weekend(d: datetime.date) -> bool:
        return (
            DateRules.calculate_dates()["this_week_sat"]
            <= d
            <= DateRules.calculate_dates()["this_week_sun"]
        )

    @staticmethod
    def in_next_week_range(d: datetime.date) -> bool:
        if DateRules.calculate_dates()["wd"] == 6:
            return (
                DateRules.calculate_dates()["next_week_tue"]
                <= d
                <= DateRules.calculate_dates()["next_week_sun"]
            )
        return (
            DateRules.calculate_dates()["next_week_mon"]
            <= d
            <= DateRules.calculate_dates()["next_week_sun"]
        )

    @staticmethod
    def is_exactly_on(
        d: datetime.date,
        item_type: Optional[ItemType],
        start_at: Optional[datetime],
        end_at: Optional[datetime],
    ) -> bool:
        s, e = DateRules.item_date_span(item_type, start_at, end_at)
        return s == d and e == d

    @staticmethod
    def fixed_period_for(group: ItemGroup) -> Optional[Period]:
        result: Optional[Period] = None
        if group == ItemGroup.TODAY:
            result = Period(
                start=DateRules._today,
                end=DateRules._today,
                inclusive=True,
                duration=1,
            )
        elif group == ItemGroup.TOMORROW:
            d = DateRules._today + timedelta(days=1)
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == ItemGroup.REST_OF_THIS_WEEK:
            w_start = max(
                DateRules._today + timedelta(days=2),
                DateRules._today,
            )
            w_end = DateRules.calculate_dates()["this_week_fri"]
            w_start = min(w_start, w_end)
            result = Period(
                start=w_start,
                end=w_end,
                inclusive=True,
                duration=(w_end - w_start).days + 1,
            )
        elif group == ItemGroup.THIS_FRIDAY:
            d = DateRules.calculate_dates()["this_week_fri"]
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == ItemGroup.THIS_WEEKEND:
            ws, we = (
                DateRules.calculate_dates()["this_week_sat"],
                DateRules.calculate_dates()["this_week_sun"],
            )
            result = Period(
                start=ws, end=we, inclusive=True, duration=(we - ws).days + 1
            )
        elif group == ItemGroup.THIS_SUNDAY:
            d = DateRules.calculate_dates()["this_week_sun"]
            result = Period(start=d, end=d, inclusive=True, duration=1)
        elif group == ItemGroup.NEXT_WEEK:
            start = (
                DateRules.calculate_dates()["next_week_tue"]
                if DateRules.calculate_dates()["wd"] == 6
                else DateRules.calculate_dates()["next_week_mon"]
            )
            end = DateRules.calculate_dates()["next_week_sun"]
            start = min(start, end)
            result = Period(
                start=start,
                end=end,
                inclusive=True,
                duration=(end - start).days + 1,
            )
        elif group == ItemGroup.REST_OF_THIS_MONTH:
            m_start = max(
                DateRules.calculate_dates()["next_week_sun"] + timedelta(days=1),
                DateRules.calculate_dates()["first_this_month"],
            )
            m_end = DateRules.calculate_dates()["last_this_month"]
            m_start = min(m_start, m_end)
            result = Period(
                start=m_start,
                end=m_end,
                inclusive=True,
                duration=(m_end - m_start).days + 1,
            )
        elif group == ItemGroup.NEXT_MONTH:
            result = Period(
                start=DateRules.calculate_dates()["first_next_month"],
                end=DateRules.calculate_dates()["last_next_month"],
                inclusive=True,
                duration=(
                    DateRules.calculate_dates()["last_next_month"]
                    - DateRules.calculate_dates()["first_next_month"]
                ).days
                + 1,
            )
        return result

    @staticmethod
    def calculate_dates() -> Dict[str, date]:
        wd = DateRules._today.weekday()
        y_man, m_man = DateRules._month_after_next(DateRules._today)
        y_next, m_next = DateRules._next_month(DateRules._today)
        this_week_sun = DateRules._today + timedelta(days=6 - wd)
        next_week_mon = this_week_sun + timedelta(days=1)
        first_next_month = DateRules._first_day(y_next, m_next)
        first_month_after_next = DateRules._first_day(y_man, m_man)
        return {
            "wd": wd,
            "this_week_fri": DateRules._today + timedelta(days=4 - wd),
            "this_week_sat": DateRules._today + timedelta(days=5 - wd),
            "this_week_sun": this_week_sun,
            "next_week_mon": next_week_mon,
            "next_week_tue": next_week_mon + timedelta(days=1),
            "next_week_sun": next_week_mon + timedelta(days=6),
            "first_this_month": DateRules._first_day(
                DateRules._today.year, DateRules._today.month
            ),
            "first_next_month": first_next_month,
            "last_this_month": first_next_month - timedelta(days=1),
            "first_month_after_next": first_month_after_next,
            "last_next_month": first_month_after_next - timedelta(days=1),
        }


PlannedItemDateRules = DateRules
