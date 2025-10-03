# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

from typing import Optional

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .exceptions import AuthConfigError
from .file_token_storage import FileTokenStorage
from .settings import AuthSettings
from .token_storage import TokenStorage


class DefaultCredentialsProvider:
    def get(
        self, settings: AuthSettings, storage: Optional[TokenStorage]
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
        creds = (
            flow.run_local_server(port=settings.oauth_port)
            if settings.use_console_oauth
            else flow.run_local_server(port=settings.oauth_port)
        )
        storage.write(creds)
        return creds
