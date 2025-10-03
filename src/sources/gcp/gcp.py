# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from datetime import date
from typing import Dict, Final, List, Optional

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.model import PlannedItem, PlannedItemList
from src.sources.gcp.data.config import TaskQueryConfig
from src.sources.gcp.google_planned_source import EnvClock, GooglePlannedSource
from src.sources.gcp.services.default_factory import \
    DefaultGoogleServiceFactory
from src.sources.gcp.services.factory import GoogleServiceFactory

_PARAMS = ParameterLoader()
DEFAULT_TODAY: Final[date] = _PARAMS.get("TODAY")
_DEFAULT_FACTORY: GoogleServiceFactory = DefaultGoogleServiceFactory()


def _default_source() -> GooglePlannedSource:
    return GooglePlannedSource(service_factory=_DEFAULT_FACTORY, clock=EnvClock())


def get_pending_tasks(
    planned_list: Optional[PlannedItemList] = None,
    period: Period = Period(duration=120),
    config: Optional[TaskQueryConfig] = None,
) -> List[PlannedItem]:
    return _default_source().get_pending_tasks(
        planned_list=planned_list, period=period, config=config
    )


def get_tasks_lists(max_items: int = 200) -> List[Dict[str, Optional[str]]]:
    return _default_source().get_tasks_lists(max_items=max_items)


def get_upcoming_events(
    planned_list: Optional[PlannedItemList] = None,
    period: Period = Period(start=DEFAULT_TODAY, duration=60),
    max_items: int = 200,
) -> List[PlannedItem]:
    return _default_source().get_upcoming_events(
        planned_list=planned_list, period=period, max_items=max_items
    )


def get_calendars_list(
    max_items: int = 500,
    min_access_role: str = "reader",
    show_hidden: bool = True,
) -> List[Dict[str, Optional[str]]]:
    return _default_source().get_calendars_list(
        max_items=max_items, min_access_role=min_access_role, show_hidden=show_hidden
    )


def auto_complete_parent_tasks(
    tasks: List[PlannedItem],
    planned_list: Optional[PlannedItemList] = None,
) -> int:
    return _default_source().auto_complete_parent_tasks(
        tasks=tasks, planned_list=planned_list
    )
