# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Run the web application using the uvicorn ASGI server.

This replaces ``pserve`` and waitress. Host, port, and the number of worker
threads are read from the ``[server:main]`` section of the configuration file,
and can be overridden on the command line::

    patzilla serve /path/to/patzilla.ini --port=6543 --reload
"""
import logging
import os
import typing as t

import uvicorn

from patzilla.web.config import read_ini

logger = logging.getLogger(__name__)


def serve(
    configfile: str,
    host: t.Optional[str] = None,
    port: t.Optional[int] = None,
    reload: bool = False,
    workers: t.Optional[int] = None,
) -> None:
    ini = read_ini(configfile)

    # The application factory reads the configuration file from the environment,
    # because uvicorn may invoke it within a different process.
    os.environ["PATZILLA_CONFIG"] = ini.path

    host = host or ini.server.host
    port = port or ini.server.port
    logger.info(f"Starting PatZilla on http://{host}:{port}, configuration file: {ini.path}")

    uvicorn.run(
        "patzilla.web.app:app_factory",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        reload_dirs=[os.path.dirname(os.path.dirname(os.path.abspath(__file__)))] if reload else None,
        workers=workers,
        # `X-Forwarded-*` headers are evaluated by `ProxyPrefixMiddleware`, when configured.
        proxy_headers=False,
        # Logging is configured by the application factory, using the configuration file.
        log_config=None,
    )
