# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuthSettings:
    credentials_path: Path = Path(
        os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS", "config/gcp/credentials.json")
    )
    token_path: Path = Path(os.getenv("GOOGLE_OAUTH_TOKEN", "config/gcp/token.json"))
    scopes: tuple[str, ...] = (
        "https://www.googleapis.com/auth/tasks",
        "https://www.googleapis.com/auth/calendar.readonly",
    )
    use_console_oauth: bool = bool(os.getenv("GOOGLE_OAUTH_CONSOLE", ""))
    oauth_port: int = int(os.getenv("GOOGLE_OAUTH_PORT", "0"))
