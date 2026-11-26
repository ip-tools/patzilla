# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Run the web application using uvicorn. Host, port, and the number of worker threads
are read from the `[server:main]` section of the configuration file.
"""
import logging
import os
import typing as t

import uvicorn

from patzilla.web.settings import WebSettings

logger = logging.getLogger(__name__)


def serve(
    configfile: str,
    host: t.Optional[str] = None,
    port: t.Optional[int] = None,
    reload: bool = False,
    workers: t.Optional[int] = None,
) -> None:
    settings = WebSettings.from_ini(configfile)

    # The application factory reads the configuration file from the environment,
    # because uvicorn may invoke it within a different process.
    os.environ["PATZILLA_CONFIG"] = str(settings.configfile)

    host = host or settings.server.host
    port = port or settings.server.port
    logger.info(f"Starting PatZilla on http://{host}:{port}, configuration file: {settings.configfile}")

    uvicorn.run(
        "patzilla.web.app:app_factory",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[os.path.dirname(os.path.dirname(os.path.abspath(__file__)))] if reload else None,
        workers=workers,
        # `X-Forwarded-*` headers are evaluated by the application, when configured.
        proxy_headers=False,
        log_config=None,
    )
