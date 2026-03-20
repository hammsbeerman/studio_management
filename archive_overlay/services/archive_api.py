from __future__ import annotations

from django.conf import settings
import requests


class ArchiveApiClient:
    def __init__(self):
        self.base_url = getattr(settings, "ARCHIVE_API_BASE_URL", "").rstrip("/")
        if not self.base_url:
            raise ValueError("ARCHIVE_API_BASE_URL is not configured in settings")

        self.timeout = int(getattr(settings, "ARCHIVE_API_TIMEOUT", 15))

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.get(url, params=params or {}, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, folder_id: int | None = None, page: int = 1):
        params = {"q": query, "page": page}
        if folder_id:
            params["folder_id"] = folder_id
        return self._get("search/", params)

    def item(self, item_id: str):
        return self._get(f"items/{item_id}/")