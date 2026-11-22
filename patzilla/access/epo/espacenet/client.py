import atexit
import logging
from concurrent.futures import Future
from queue import Queue
from threading import Lock, Thread

import json
from dataclasses import dataclass
from typing import Optional

from espacenet_cli.utils.edge_backend import EspacenetBackend
from requests import Response


_STOP = object()
_requests = Queue()
_lock = Lock()
_worker = None
_closed = False


logger = logging.getLogger(__name__)


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


def _run_backend():
    backend = None
    try:
        while True:
            item = _requests.get()
            if item is _STOP:
                return

            url, future = item
            try:
                if backend is None:
                    backend = EspacenetBackend.create(mode="background")

                response = backend.fetch(url)
                future.set_result(
                    Response(
                        url=url,
                        status_code=response["status"],
                        text=response["text"],
                    )
                )
            except Exception as error:

                if backend is not None:
                    try:
                        browser = backend._browser
                        disconnected = browser is None or not browser.is_connected()
                    except Exception:
                        logger.exception("Could not check Espacenet browser connection")
                    else:
                        if disconnected:
                            stale_backend, backend = backend, None
                            try:
                                stale_backend.close()
                            except Exception:
                                logger.exception("Could not close disconnected Espacenet backend")

                future.set_exception(error)
    finally:
        if backend is not None:
            backend.close()


def close_espacenet_backend():
    """Drain queued requests and close the backend on its owner thread."""
    global _closed

    with _lock:
        if not _closed:
            _closed = True
            if _worker is not None:
                _requests.put(_STOP)
        worker = _worker

    if worker is not None:
        worker.join()


atexit.register(close_espacenet_backend)


class EspacenetClient:
    """
    Adapter for Espacenet using `espacenet-cli`.
    https://pypi.org/project/espacenet-cli/

    playwright install --with-deps msedge
    """
    def fetch(self, url):
        """Fetch URL and return a `requests`-like response."""
        global _worker

        future = Future()
        with _lock:
            if _closed:
                raise RuntimeError("Espacenet backend is closed")

            if _worker is None:
                worker = Thread(
                    target=_run_backend,
                    name="espacenet-backend",
                    daemon=True,
                )
                worker.start()
                _worker = worker

            _requests.put((url, future))

        return future.result()
