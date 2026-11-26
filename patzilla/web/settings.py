# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Web application settings, read from the `[app:main]`, `[filter:*]`, and `[server:main]`
sections of the INI file. The file format is retained from PasteDeploy times.
"""
import os
import typing as t
from configparser import ConfigParser, InterpolationError
from pathlib import Path

from pydantic import BaseModel, Field

from patzilla.util.config import asbool

PROXY_FILTER = "egg:PasteDeploy#prefix"


class ProxySettings(BaseModel):
    # Trust `X-Forwarded-*` headers from these hosts, and serve below this path prefix.
    trusted_hosts: str = "*"
    root_path: str = ""


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 6543
    threads: t.Optional[int] = None


class WebSettings(BaseModel):
    configfile: Path
    flavor: t.Literal["web", "minimal"] = "web"
    mongodb_uri: t.Optional[str] = None
    reload_templates: bool = False
    api_docs: bool = False
    proxy: t.Optional[ProxySettings] = None
    server: ServerSettings = Field(default_factory=ServerSettings)
    # All `[app:main]` settings, e.g. `cache.*`.
    app: t.Dict[str, str] = Field(default_factory=dict)
    has_logging: bool = False

    @classmethod
    def from_ini(cls, path: t.Union[str, Path]) -> "WebSettings":
        path = Path(path).absolute()
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        parser = ConfigParser(defaults={"here": str(path.parent), "__file__": str(path)})
        parser.optionxform = str  # type: ignore[assignment,method-assign]
        parser.read(path)

        app = _section(parser, "app:main")
        flavor = app.pop("use", "#web").rsplit("#", 1)[-1] or "web"
        proxy = None
        filter_name = app.pop("filter-with", None)
        if filter_name:
            options = _section(parser, f"filter:{filter_name}")
            if options.get("use", "").strip() != PROXY_FILTER:
                raise ValueError(f"Unsupported filter `{filter_name}`, only `{PROXY_FILTER}` is supported")
            proxy = ProxySettings(root_path=options.get("prefix", "").rstrip("/"))
        server = _section(parser, "server:main")
        server.pop("use", None)

        return cls(
            configfile=path,
            flavor=flavor,  # type: ignore[arg-type]
            mongodb_uri=app.get("mongodb.patzilla.uri"),
            reload_templates=asbool(app.get("reload_templates", app.get("pyramid.reload_templates"))),
            api_docs=asbool(app.get("api.docs")),
            proxy=proxy,
            server=ServerSettings(**server),
            app=app,
            has_logging=parser.has_section("loggers"),
        )

    @classmethod
    def from_environment(cls) -> "WebSettings":
        configfile = os.environ.get("PATZILLA_CONFIG")
        if not configfile:
            raise ValueError("Configuration file missing, please set the PATZILLA_CONFIG environment variable")
        return cls.from_ini(configfile)


def _section(parser: ConfigParser, name: str) -> t.Dict[str, str]:
    """Read a section, resolving `%(here)s` like PasteDeploy, using raw values otherwise."""
    if not parser.has_section(name):
        return {}
    result = {}
    for key in parser.options(name):
        if key in ("here", "__file__"):
            continue
        try:
            result[key] = parser.get(name, key)
        except InterpolationError:
            result[key] = parser.get(name, key, raw=True)
    return result
