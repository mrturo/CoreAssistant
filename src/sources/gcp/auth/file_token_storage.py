# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from google.auth.exceptions import GoogleAuthError
from google.oauth2.credentials import Credentials


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
