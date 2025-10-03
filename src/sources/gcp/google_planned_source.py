# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from typing import (Callable, Dict, Final, Iterable, Iterator, List, Optional,
                    Tuple)
from zoneinfo import ZoneInfo

from googleapiclient.discovery import Resource

from src.common.data.parameters import ParameterLoader
from src.common.datetime.period import Period
from src.common.hierarchy.hierarchy_builder import HierarchyBuilder
from src.common.hierarchy.parent_policy import ParentPolicy
from src.model import ItemStatus, PlannedItem, PlannedItemList
from src.sources.gcp.auth.settings import AuthSettings
from src.sources.gcp.data.auto_completer import TaskAutoCompleter
from src.sources.gcp.data.config import TaskQueryConfig
from src.sources.gcp.data.enricher import TaskEnricher
from src.sources.gcp.data.fetcher import TaskFetcher
from src.sources.gcp.data.updater import TaskUpdater
from src.sources.gcp.env_clock import EnvClock
from src.sources.gcp.mappers.calendar_events import GoogleCalendarEventsMapper
from src.sources.gcp.mappers.tasks import GoogleTasksMapper
from src.sources.gcp.services.default_factory import \
    DefaultGoogleServiceFactory
from src.sources.gcp.services.factory import GoogleServiceFactory

_PARAMS = ParameterLoader()
DEFAULT_TODAY: Final[date] = _PARAMS.get("TODAY")
DEFAULT_CALENDAR_ID: Final[str] = "primary"
DEFAULT_TASKLIST_ID: Final[str] = "@default"
TASKS_PAGE_CAP: Final[int] = 100
CALENDAR_LIST_PAGE_CAP: Final[int] = 250
EVENTS_PAGE_CAP: Final[int] = 250
_DEFAULT_FACTORY: GoogleServiceFactory = DefaultGoogleServiceFactory()


def _is_past(now: datetime, it: PlannedItem) -> bool:
    s = it.start_at
    e = it.end_at
    if e is not None and e < now:
        return True
    if s is not None and e is None and s < now:
        return True
    return False


def _scoped_settings(
    settings: Optional[AuthSettings],
    scopes: Optional[Iterable[str]],
) -> AuthSettings:
    eff = settings or AuthSettings()
    return eff if not scopes else replace(eff, scopes=tuple(scopes))


def _local_day_bounds(d: date, tz: ZoneInfo) -> Tuple[datetime, datetime, datetime]:
    start = datetime.combine(d, time.min, tzinfo=tz)
    end_inclusive = datetime.combine(d, time.max, tzinfo=tz)
    end_exclusive = start + timedelta(days=1)
    return start, end_inclusive, end_exclusive


def _paginate(
    fetch_page: Callable[[Optional[str], int], Dict],
    max_items: int,
    page_size_cap: int,
) -> Iterator[Dict]:
    results_count = 0
    page_token: Optional[str] = None
    while True:
        remaining = max(1, max_items - results_count)
        resp = fetch_page(page_token, min(page_size_cap, remaining))
        items = resp.get("items", []) or []
        for it in items:
            yield it
            results_count += 1
            if results_count >= max_items:
                return
        page_token = resp.get("nextPageToken")
        if not page_token:
            return


class GooglePlannedSource:
    def __init__(
        self,
        service_factory: GoogleServiceFactory = _DEFAULT_FACTORY,
        auth_settings: Optional[AuthSettings] = None,
        clock: EnvClock = EnvClock(),
    ) -> None:
        self._factory = service_factory
        self._auth_settings = auth_settings
        self._clock = clock

    def _get_service(
        self,
        api_name: str,
        api_version: str,
        scopes: Optional[Iterable[str]] = None,
    ) -> Resource:
        eff_settings = _scoped_settings(self._auth_settings, scopes)
        return self._factory.build(api_name, api_version, settings=eff_settings)

    def get_pending_tasks(
        self,
        planned_list: Optional[PlannedItemList] = None,
        period: Period = Period(duration=120),
        config: Optional[TaskQueryConfig] = None,
    ) -> List[PlannedItem]:
        config = config or TaskQueryConfig()
        planned_list = planned_list or PlannedItemList(
            kind="tasklist", id=DEFAULT_TASKLIST_ID
        )
        service = self._get_service(api_name="tasks", api_version="v1")
        start_dt, _, _ = _local_day_bounds(period.start, self._clock.tzinfo)
        _, end_dt_last, _ = _local_day_bounds(period.end, self._clock.tzinfo)
        fetcher = TaskFetcher(service, planned_list)
        fetcher.fetch_dated_tasks(config.max_items, start_dt, end_dt_last)
        fetcher.fetch_undated_tasks(config.max_items, config.include_undated)
        enricher = TaskEnricher(config, planned_list)
        enriched = enricher.enrich_items(fetcher.all_items)
        builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
        tasks = builder.build(enriched, GoogleTasksMapper())
        return [t for t in tasks if t.is_root() and t.status == ItemStatus.NEEDS_ACTION]

    def get_tasks_lists(
        self,
        max_items: int = 200,
    ) -> List[Dict[str, Optional[str]]]:
        service = self._get_service(api_name="tasks", api_version="v1")

        def _fetch(page_token: Optional[str], max_results: int) -> Dict:
            return (
                service.tasklists()
                .list(maxResults=max_results, pageToken=page_token)
                .execute()
            )

        results: List[Dict[str, Optional[str]]] = []
        for it in _paginate(_fetch, max_items=max_items, page_size_cap=TASKS_PAGE_CAP):
            results.append(
                {
                    "id": it.get("id", ""),
                    "title": it.get("title", ""),
                    "updated": it.get("updated"),
                    "self_link": it.get("selfLink"),
                }
            )
        return results

    def get_upcoming_events(
        self,
        planned_list: Optional[PlannedItemList] = None,
        period: Period = Period(start=DEFAULT_TODAY, duration=60),
        max_items: int = 200,
    ) -> List[PlannedItem]:
        planned_list = planned_list or PlannedItemList(
            kind="calendar", id=DEFAULT_CALENDAR_ID
        )
        service_calendar = self._get_service(api_name="calendar", api_version="v3")
        time_min = f"{period.start.isoformat()}T00:00:00Z"
        time_max = f"{period.end.isoformat()}T23:59:59Z"

        def _fetch(page_token: Optional[str], max_results: int) -> Dict:
            return (
                service_calendar.events()
                .list(
                    calendarId=planned_list.id,
                    singleEvents=True,
                    maxResults=max_results,
                    pageToken=page_token,
                    timeMin=time_min,
                    timeMax=time_max,
                )
                .execute()
            )

        all_items: List[Dict] = []
        for item in _paginate(
            _fetch, max_items=max_items, page_size_cap=EVENTS_PAGE_CAP
        ):
            item["plannedItemList"] = planned_list
            all_items.append(item)
        builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
        events = builder.build(all_items, GoogleCalendarEventsMapper())
        now = self._clock.now
        return [it for it in events if not _is_past(now, it)]

    def get_calendars_list(
        self,
        max_items: int = 500,
        min_access_role: str = "reader",
        show_hidden: bool = True,
    ) -> List[Dict[str, Optional[str]]]:
        service = self._get_service(api_name="calendar", api_version="v3")

        def _fetch(page_token: Optional[str], max_results: int) -> Dict:
            return (
                service.calendarList()
                .list(
                    maxResults=max_results,
                    pageToken=page_token,
                    minAccessRole=min_access_role,
                    showHidden=show_hidden,
                )
                .execute()
            )

        results: List[Dict[str, Optional[str]]] = []
        for it in _paginate(
            _fetch, max_items=max_items, page_size_cap=CALENDAR_LIST_PAGE_CAP
        ):
            results.append(
                {
                    "id": it.get("id", ""),
                    "summary": it.get("summary", it.get("id", "")),
                    "primary": bool(it.get("primary", False)),
                    "access_role": it.get("accessRole", ""),
                    "time_zone": it.get("timeZone"),
                    "selected": it.get("selected"),
                    "background_color": it.get("backgroundColor"),
                }
            )
        return results

    def auto_complete_parent_tasks(
        self,
        tasks: List[PlannedItem],
        planned_list: Optional[PlannedItemList] = None,
    ) -> int:
        planned_list = planned_list or PlannedItemList(
            kind="tasklist", id=DEFAULT_TASKLIST_ID
        )
        service = self._get_service(api_name="tasks", api_version="v1")
        updater = TaskUpdater(service, planned_list)
        auto_completer = TaskAutoCompleter(updater)

        return auto_completer.process_tasks_for_auto_completion(tasks)
