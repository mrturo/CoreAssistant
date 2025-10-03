# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=no-member
# pylint: disable=E0401
# pyright: reportMissingImports=false

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from datetime import time as dtime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol
from zoneinfo import ZoneInfo

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from src.mappers.google_calendar_events_mapper import \
    GoogleCalendarEventsMapper
from src.mappers.google_tasks_mapper import GoogleTasksMapper
from src.model.planned_item import PlannedItem, PlannedItemStatus
from src.model.planned_item_list import PlannedItemList
from src.planned_item.hierarchy_builder import HierarchyBuilder, ParentPolicy
from src.util.parameters import ParameterLoader
from src.util.period import Period

params = ParameterLoader()
tzinfo: ZoneInfo = params.get("TZINFO")
today: datetime.date = params.get("TODAY")
now: datetime = params.get("NOW")

DEFAULT_CALENDAR_ID = "primary"
DEFAULT_TASKLIST_ID = "@default"
DEFAULT_SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
)


def _rfc3339_utc(dt: datetime) -> str:
    return dt.astimezone(tzinfo).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class AuthSettings:
    credentials_path: Path = Path(
        os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "config/gcp/credentials.json")
    )
    token_path: Path = Path(os.getenv("GOOGLE_OAUTH_TOKEN", "config/gcp/token.json"))
    scopes: tuple[str, ...] = DEFAULT_SCOPES
    use_console_oauth: bool = bool(os.getenv("GOOGLE_OAUTH_CONSOLE", ""))
    oauth_port: int = int(os.getenv("GOOGLE_OAUTH_PORT", "0"))


class TokenStorage(Protocol):
    def read(self, scopes: Iterable[str]) -> Optional[Credentials]:
        raise NotImplementedError

    def write(self, creds: Credentials) -> None:
        raise NotImplementedError


class FileTokenStorage:
    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self, scopes: Iterable[str]) -> Optional[Credentials]:
        if not self._path.exists():
            return None
        try:
            return Credentials.from_authorized_user_file(str(self._path), list(scopes))
        except (ValueError, GoogleAuthError) as exc:
            print(f"Invalid token in {self._path}: {exc}")
            return None

    def write(self, creds: Credentials) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = creds.to_json()
        json.loads(serialized)
        self._path.write_text(serialized, encoding="utf-8")


class AuthConfigError(RuntimeError): ...


def obtain_credentials(
    settings: AuthSettings,
    storage: Optional[TokenStorage] = None,
) -> Credentials:
    storage = storage or FileTokenStorage(settings.token_path)
    scopes = settings.scopes
    creds = storage.read(scopes)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            storage.write(creds)
            return creds
        except GoogleAuthError as exc:
            print(f"Token refresh failed: {exc}")
    if not settings.credentials_path.exists():
        raise AuthConfigError(
            f"Missing '{settings.credentials_path}'. "
            "Download it from Google Cloud Console (OAuth client - Desktop)."
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        str(settings.credentials_path), list(scopes)
    )
    if settings.use_console_oauth:
        creds = flow.run_console()
    else:
        creds = flow.run_local_server(port=settings.oauth_port)
    storage.write(creds)
    return creds


def build_google_service(
    api_name: str,
    api_version: str,
    settings: Optional[AuthSettings] = None,
    storage: Optional[TokenStorage] = None,
) -> Resource:
    settings = settings or AuthSettings()
    creds = obtain_credentials(settings=settings, storage=storage)
    return build(api_name, api_version, credentials=creds)  # type: ignore[no-any-return]


def get_task_service(
    scopes: Optional[Iterable[str]] = None,
    settings: Optional[AuthSettings] = None,
) -> Resource:
    if scopes:
        eff_settings = settings or AuthSettings()
        eff_settings = AuthSettings(
            credentials_path=eff_settings.credentials_path,
            token_path=eff_settings.token_path,
            scopes=tuple(scopes),
            use_console_oauth=eff_settings.use_console_oauth,
            oauth_port=eff_settings.oauth_port,
        )
    else:
        eff_settings = settings or AuthSettings()
    return build_google_service("tasks", "v1", settings=eff_settings)


def get_pending_tasks(
    planned_list: Optional[PlannedItemList] = None,
    period: Period = Period(duration=120),
    max_items: int = 200,
) -> List[PlannedItem]:
    if planned_list is None:
        planned_list = PlannedItemList(kind="tasklist", id=DEFAULT_TASKLIST_ID)
    service = get_task_service()
    all_items: list[dict] = []
    page_token: Optional[str] = None
    start_dt = datetime.combine(period.start, dtime.min, tzinfo=tzinfo)
    end_dt = datetime.combine(period.end, dtime.max, tzinfo=tzinfo)
    while True:
        remaining = max(1, max_items - len(all_items))
        req = service.tasks().list(
            tasklist=planned_list.id,
            showCompleted=True,
            showHidden=True,
            showDeleted=False,
            maxResults=min(100, remaining),
            pageToken=page_token,
            dueMin=_rfc3339_utc(start_dt),
            dueMax=_rfc3339_utc(end_dt),
        )
        resp = req.execute()
        items = resp.get("items", [])
        if items:
            for item in items:
               item["plannedItemList"] = planned_list
            all_items.extend(items)
        page_token = resp.get("nextPageToken")
        if not page_token or len(all_items) >= max_items:
            break
    page_token: Optional[str] = None
    while True:
        remaining = max(1, max_items - len(all_items))
        req = service.tasks().list(
            tasklist=planned_list.id,
            showCompleted=True,
            showHidden=True,
            showDeleted=False,
            maxResults=min(100, remaining),
            pageToken=page_token,
        )
        resp = req.execute()
        items = resp.get("items", [])
        items = [t for t in items if "start" not in t]
        if items:
            for item in items:
                item["plannedItemList"] = planned_list
            all_items.extend(items)
        page_token = resp.get("nextPageToken")
        if not page_token or len(all_items) >= max_items:
            break
    builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
    tasks = builder.build(all_items, GoogleTasksMapper())
    tasks = [
        t for t in tasks if t.is_root() and t.status == PlannedItemStatus.NEEDS_ACTION
    ]
    return tasks


def list_tasks(
    max_items: int = 200,
) -> list[dict[str, Optional[str]]]:
    service = get_task_service()
    results: list[dict[str, Optional[str]]] = []
    page_token: Optional[str] = None
    while True:
        remaining = max(1, max_items - len(results))
        req = service.tasklists().list(
            maxResults=min(100, remaining),
            pageToken=page_token,
        )
        resp = req.execute()
        items = resp.get("items", [])
        for it in items:
            results.append(
                {
                    "id": it.get("id", ""),
                    "title": it.get("title", ""),
                    "updated": it.get("updated"),
                    "self_link": it.get("selfLink"),
                }
            )
        page_token = resp.get("nextPageToken")
        if not page_token or len(results) >= max_items:
            break
    return results


def get_calendar_service(
    scopes: Optional[Iterable[str]] = None,
    settings: Optional[AuthSettings] = None,
) -> Resource:
    if scopes:
        eff_settings = settings or AuthSettings()
        eff_settings = AuthSettings(
            credentials_path=eff_settings.credentials_path,
            token_path=eff_settings.token_path,
            scopes=tuple(scopes),
            use_console_oauth=eff_settings.use_console_oauth,
            oauth_port=eff_settings.oauth_port,
        )
    else:
        eff_settings = settings or AuthSettings()
    return build_google_service("calendar", "v3", settings=eff_settings)


def get_upcoming_events(
    planned_list: Optional[PlannedItemList] = None,
    period: Period = Period(start=today, duration=60),
    max_items: int = 200,
) -> List[PlannedItem]:
    if planned_list is None:
        planned_list = PlannedItemList(kind="calendar", id=DEFAULT_CALENDAR_ID)
    service_calendar = get_calendar_service()
    all_items: list[dict] = []
    page_token: Optional[str] = None
    while True:
        remaining = max(1, max_items - len(all_items))
        req = service_calendar.events().list(
            calendarId=planned_list.id,
            singleEvents=True,
            maxResults=min(100, remaining),
            pageToken=page_token,
            timeMin=period.start.isoformat() + "T00:00:00Z",
            timeMax=period.end.isoformat() + "T23:59:59Z",
        )
        resp = req.execute()
        items = resp.get("items", [])
        if items:
            for item in items:
                item["plannedItemList"] = planned_list
            all_items.extend(items)
        page_token = resp.get("nextPageToken")
        if not page_token or len(all_items) >= max_items:
            break
    builder = HierarchyBuilder(parent_policy=ParentPolicy.LENIENT)
    events = builder.build(all_items, GoogleCalendarEventsMapper())

    def _is_past(it: PlannedItem) -> bool:
        s = it.start_at
        e = it.end_at
        if e is not None and e < now:
            return True
        if s is not None and e is None and s < now:
            return True
        return False

    events = [it for it in events if not _is_past(it)]
    return events


def list_calendars(
    max_items: int = 500,
    min_access_role: str = "reader",
    show_hidden: bool = True,
) -> List[Dict[str, Optional[str]]]:
    service = get_calendar_service()
    results: List[Dict[str, Optional[str]]] = []
    page_token: Optional[str] = None
    while True:
        remaining = max(1, max_items - len(results))
        req = service.calendarList().list(
            maxResults=min(250, remaining),
            pageToken=page_token,
            minAccessRole=min_access_role,
            showHidden=show_hidden,
        )
        resp = req.execute()
        items = resp.get("items", [])
        for it in items:
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
        page_token = resp.get("nextPageToken")
        if not page_token or len(results) >= max_items:
            break
    return results
