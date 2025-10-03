# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional, Protocol

from google.oauth2.credentials import Credentials

from .settings import AuthSettings
from .token_storage import TokenStorage


class CredentialsProvider(Protocol):
    def get(
        self, settings: AuthSettings, storage: Optional[TokenStorage]
    ) -> Credentials: ...
