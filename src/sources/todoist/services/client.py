# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.sources.todoist.auth.settings import TodoistAuthSettings


class TodoistClient:
    def __init__(self, settings: Optional[TodoistAuthSettings] = None) -> None:
        self.settings = settings or TodoistAuthSettings()
        self.headers = {
            "Authorization": f"Bearer {self.settings.api_token}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, 
        endpoint: str, 
        method: str = "GET", 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url = f"{self.settings.base_url}/{endpoint.lstrip('/')}"
        
        if params:
            url += f"?{urlencode(params)}"
        
        req_data = json.dumps(data).encode('utf-8') if data else None
        
        try:
            request = Request(url, data=req_data, headers=self.headers, method=method)
            
            with urlopen(request) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data) if response_data else {}
                
        except HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.reason}"
            if hasattr(e, 'read'):
                error_body = e.read().decode('utf-8')
                try:
                    error_data = json.loads(error_body)
                    error_msg += f" - {error_data}"
                except json.JSONDecodeError:
                    error_msg += f" - {error_body}"
            raise ValueError(f"Todoist API error: {error_msg}") from e
            
        except URLError as e:
            raise ValueError(f"Network error: {e.reason}") from e

    def get_tasks(
        self, 
        project_id: Optional[str] = None,
        section_id: Optional[str] = None,
        label: Optional[str] = None,
        filter_query: Optional[str] = None,
        lang: str = "en"
    ) -> List[Dict[str, Any]]:
        params = {"lang": lang}
        
        if project_id:
            params["project_id"] = project_id
        if section_id:
            params["section_id"] = section_id
        if label:
            params["label"] = label
        if filter_query:
            params["filter"] = filter_query
            
        return self._make_request("tasks", params=params)

    def get_projects(self) -> List[Dict[str, Any]]:
        return self._make_request("projects")

    def get_sections(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if project_id:
            params["project_id"] = project_id
        return self._make_request("sections", params=params)

    def get_labels(self) -> List[Dict[str, Any]]:
        return self._make_request("labels")

    def complete_task(self, task_id: str) -> bool:
        try:
            self._make_request(f"tasks/{task_id}/close", method="POST")
            return True
        except Exception as e:
            print(f"Error completing task {task_id}: {e}")
            return False

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request("tasks", method="POST", data=task_data)

    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_request(f"tasks/{task_id}", method="POST", data=task_data)