# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv  # type: ignore


class ParameterLoader:
    _ENV_FILEPATH = ".env"

    def __init__(self) -> None:
        self._params: dict[str, Any] = {}
        self.env_filepath = Path(ParameterLoader._ENV_FILEPATH)
        load_dotenv(dotenv_path=self.env_filepath)
        self._load_base_parameters()

    def _load_base_parameters(self) -> None:
        time_zone = os.getenv("TIME_ZONE")
        tzinfo: ZoneInfo = datetime.now().astimezone().tzinfo
        if time_zone and isinstance(time_zone, str) and len(time_zone.strip()) > 0:
            tzinfo = ZoneInfo(time_zone.strip())
        ignored_lists: list[str] = []
        raw_ignored_lists = os.getenv("IGNORED_LISTS")
        if (
            raw_ignored_lists
            and isinstance(raw_ignored_lists, str)
            and len(raw_ignored_lists.strip()) > 0
        ):
            ignored_lists = raw_ignored_lists.split(",")
        custom_date: Optional[datetime] = None
        now: datetime = custom_date or datetime.now(tzinfo)
        self._params["TZINFO"] = tzinfo
        self._params["NOW"] = now
        self._params["TODAY"] = now.date()
        self._params["IGNORED_LISTS"] = ignored_lists

    def get(self, key: str) -> Any:
        if key not in self._params:
            raise KeyError(f"Parameter '{key}' not found.")
        return self._params[key]

    def set(self, key: str, value: Any) -> None:
        self._params[key] = value
