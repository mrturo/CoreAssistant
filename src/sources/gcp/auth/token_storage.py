# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Iterable, Optional, Protocol

from google.oauth2.credentials import Credentials


class TokenStorage(Protocol):
    def read(self, scopes: Iterable[str]) -> Optional[Credentials]:
        raise NotImplementedError

    def write(self, creds: Credentials) -> None:
        raise NotImplementedError
