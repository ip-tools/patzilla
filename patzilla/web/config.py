# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Read the PasteDeploy-style INI configuration file.

The file format is retained for compatibility with existing installations:

- ``[app:main]``: Application settings, e.g. ``mongodb.patzilla.uri`` and ``cache.*``.
  ``use = egg:patzilla#web`` selects the application flavor (``web`` or ``minimal``).
  ``filter-with = <name>`` enables the ``[filter:<name>]`` reverse proxy middleware.
- ``[filter:<name>]``: Options for the reverse proxy middleware, i.e. ``prefix``,
  ``translate_forwarded_server``, ``force_port``, and ``scheme``.
- ``[server:main]``: ``host``, ``port``, and ``threads`` for the HTTP server.
- ``[loggers]`` etc.: Logging configuration.

All other sections are read by ``patzilla.navigator.settings.GlobalSettings``.
"""
import dataclasses
import logging
import os
import typing as t
from configparser import ConfigParser, InterpolationError

from patzilla.util.config import asbool

logger = logging.getLogger(__name__)

PROXY_FILTER = "egg:PasteDeploy#prefix"


@dataclasses.dataclass
class ProxyOptions:
    prefix: str = ""
    translate_forwarded_server: bool = True
    force_port: t.Optional[str] = None
    scheme: t.Optional[str] = None


@dataclasses.dataclass
class ServerOptions:
    host: str = "0.0.0.0"
    port: int = 6543
    threads: t.Optional[int] = None


@dataclasses.dataclass
class IniConfiguration:
    path: str
    flavor: str = "web"
    settings: t.Dict[str, str] = dataclasses.field(default_factory=dict)
    proxy: t.Optional[ProxyOptions] = None
    server: ServerOptions = dataclasses.field(default_factory=ServerOptions)
    has_logging: bool = False


def _section(parser: ConfigParser, name: str) -> t.Dict[str, str]:
    """
    Read a section, resolving ``%(here)s`` and ``%(__file__)s`` like PasteDeploy.
    Values which can not be interpolated are used verbatim.
    """
    result = {}
    for key in parser.options(name):
        if key in ("here", "__file__"):
            continue
        try:
            result[key] = parser.get(name, key)
        except InterpolationError:
            result[key] = parser.get(name, key, raw=True)
    return result


def read_ini(path: str) -> IniConfiguration:
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")
    parser = ConfigParser(defaults={"here": os.path.dirname(path), "__file__": path})
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    parser.read(path)

    config = IniConfiguration(path=path)
    config.has_logging = parser.has_section("loggers")

    if parser.has_section("app:main"):
        settings = _section(parser, "app:main")
        use = settings.pop("use", "")
        if "#" in use:
            config.flavor = use.rsplit("#", 1)[1].strip() or "web"
        filter_name = settings.pop("filter-with", None)
        options = _section(parser, f"filter:{filter_name}") if filter_name and parser.has_section(f"filter:{filter_name}") else {}
        if filter_name and options.pop("use", "").strip() != PROXY_FILTER:
            logger.warning(f"Ignoring unsupported filter `{filter_name}`, only `{PROXY_FILTER}` is supported")
        elif filter_name:
            config.proxy = ProxyOptions(
                prefix=options.get("prefix", "").rstrip("/"),
                translate_forwarded_server=asbool(options.get("translate_forwarded_server", True)),
                force_port=options.get("force_port"),
                scheme=options.get("scheme") or None,
            )
        config.settings = settings

    if parser.has_section("server:main"):
        server = _section(parser, "server:main")
        config.server = ServerOptions(
            host=server.get("host", ServerOptions.host),
            port=int(server.get("port", ServerOptions.port)),
            threads=int(server["threads"]) if server.get("threads") else None,
        )

    return config
