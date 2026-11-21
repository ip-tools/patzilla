import json
from dataclasses import dataclass
from typing import Optional

from espacenet_cli.utils.edge_backend import EspacenetBackend
from requests import Response


@dataclass
class Response:
    """A `requests`-like response object."""
    url: Optional[str] = None
    text: Optional[str] = None
    status_code: Optional[int] = None

    def json(self):
        if self.text is None:
            raise ValueError("HTTP response is empty")
        return json.loads(self.text)

backend = None

class EspacenetClient:
    """
    Adapter for Espacenet using `espacenet-cli`.
    https://pypi.org/project/espacenet-cli/

    playwright install --with-deps msedge
    """

    def __init__(self):
        """Initialize Espacenet client based on Playwright."""
        global backend
        if backend is None:
            backend = EspacenetBackend.create()
        self.backend = backend

    def fetch(self, url):
        """Fetch URL and return a `requests`-like response."""
        response_effective = Response()
        response = self.backend.fetch(url)
        response_effective.url = url
        response_effective.status_code = response["status"]
        response_effective.text = response["text"]
        return response_effective
