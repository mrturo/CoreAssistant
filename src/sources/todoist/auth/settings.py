# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class TodoistAuthSettings:
    api_token: str = os.getenv("TODOIST_API_TOKEN", "")
    base_url: str = "https://api.todoist.com/rest/v2"
    sync_url: str = "https://api.todoist.com/sync/v9"
    
    def __post_init__(self) -> None:
        if not self.api_token:
            raise ValueError(
                "TODOIST_API_TOKEN environment variable is required. "
                "Get your token from https://todoist.com/prefs/integrations"
            )