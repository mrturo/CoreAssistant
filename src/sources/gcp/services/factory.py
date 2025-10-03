# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional, Protocol

from googleapiclient.discovery import Resource

from src.sources.gcp.auth.settings import AuthSettings
from src.sources.gcp.auth.token_storage import TokenStorage


class GoogleServiceFactory(Protocol):
    def build(
        self,
        api_name: str,
        api_version: str,
        settings: AuthSettings,
        storage: Optional[TokenStorage] = None,
    ) -> Resource: ...
