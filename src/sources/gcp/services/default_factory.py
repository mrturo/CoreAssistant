# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional

from googleapiclient.discovery import Resource, build

from src.sources.gcp.auth.credentials_provider import CredentialsProvider
from src.sources.gcp.auth.default_credentials_provider import \
    DefaultCredentialsProvider
from src.sources.gcp.auth.settings import AuthSettings
from src.sources.gcp.auth.token_storage import TokenStorage


class DefaultGoogleServiceFactory:
    def __init__(
        self, credentials_provider: Optional[CredentialsProvider] = None
    ) -> None:
        self._credentials_provider = (
            credentials_provider or DefaultCredentialsProvider()
        )

    def build(
        self,
        api_name: str,
        api_version: str,
        settings: AuthSettings,
        storage: Optional[TokenStorage] = None,
    ) -> Resource:
        creds = self._credentials_provider.get(settings=settings, storage=storage)
        # type: ignore[no-any-return]
        return build(api_name, api_version, credentials=creds)
