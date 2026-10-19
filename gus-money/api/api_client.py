"""Reusable client for the Gus Money admin BFF (`/api/proxy`).

Every backend call goes through POST/GET /api/proxy with an `x-target-endpoint` header
naming the real endpoint (e.g. /auth/login, /users). Session is cookie based.
"""
import uuid

import requests

from . import config


class APIClient:
    def __init__(self, base_url: str = config.BASE_URL, timeout: float = config.TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.device_id = str(uuid.uuid4())

    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        headers = {
            "x-target-endpoint": endpoint,
            "x-device-id": self.device_id,
            "x-client-timezone": "UTC",
            **kwargs.pop("headers", {}),
        }
        return self.session.request(
            method, f"{self.base_url}/api/proxy", headers=headers, timeout=self.timeout, **kwargs
        )

    def login(self, email: str, password: str) -> requests.Response:
        return self.request("POST", "/auth/login", json={"email": email, "password": password})

    def list_users(self, **params) -> requests.Response:
        query = {"skip": 0, "limit": 20, "scope": "customer", "sortBy": "createdAt", "sortOrder": "desc"}
        query.update(params)
        return self.request("GET", "/users", params=query)
