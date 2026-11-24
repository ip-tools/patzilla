# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
"""
Typed configuration settings for authentication (magic links and sessions).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from patzilla.util.config import asbool, read_list


DEFAULT_MAGIC_LINK_TTL_SECONDS = 900  # 15 minutes
DEFAULT_MAGIC_LINK_RATE_LIMIT_COUNT = 5
DEFAULT_MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS = 900  # 15 minutes
DEFAULT_SESSION_TTL_SECONDS = 14 * 24 * 60 * 60  # 14 days
DEFAULT_SESSION_RENEWAL_THRESHOLD_SECONDS = 7 * 24 * 60 * 60  # 7 days


@dataclass(frozen=True)
class AuthSettings:
    """
    Configuration container for the `[auth]` INI section.
    """

    magic_link_enabled: bool = True
    magic_link_allow_signup: bool = True
    magic_link_ttl_seconds: int = DEFAULT_MAGIC_LINK_TTL_SECONDS
    magic_link_rate_limit_count: int = DEFAULT_MAGIC_LINK_RATE_LIMIT_COUNT
    magic_link_rate_limit_window_seconds: int = DEFAULT_MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS
    magic_link_default_tags: tuple[str, ...] = ("self-registered",)
    magic_link_default_modules: tuple[str, ...] = ()

    session_ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS
    session_renewal_threshold_seconds: int = DEFAULT_SESSION_RENEWAL_THRESHOLD_SECONDS
    session_cookie_name: str = "patzilla_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "Lax"

    public_base_url: str = ""
    log_magic_link_in_dev: bool = True

    @classmethod
    def from_mapping(cls, data: Optional[Mapping[str, Any]]) -> AuthSettings:
        """
        Parse an `[auth]` settings mapping into a typed `AuthSettings` instance.
        """
        raw = data or {}

        default_tags = tuple(read_list(raw.get("magic_link_default_tags", "self-registered")))
        default_modules = tuple(read_list(raw.get("magic_link_default_modules", "")))

        samesite = str(raw.get("session_cookie_samesite", "Lax")).strip() or "Lax"
        if samesite not in {"Strict", "Lax", "None"}:
            samesite = "Lax"

        return cls(
            magic_link_enabled=asbool(raw.get("magic_link_enabled", True)),
            magic_link_allow_signup=asbool(raw.get("magic_link_allow_signup", True)),
            magic_link_ttl_seconds=max(
                60, int(raw.get("magic_link_ttl_seconds", DEFAULT_MAGIC_LINK_TTL_SECONDS))
            ),
            magic_link_rate_limit_count=max(
                1, int(raw.get("magic_link_rate_limit_count", DEFAULT_MAGIC_LINK_RATE_LIMIT_COUNT))
            ),
            magic_link_rate_limit_window_seconds=max(
                60,
                int(
                    raw.get(
                        "magic_link_rate_limit_window_seconds",
                        DEFAULT_MAGIC_LINK_RATE_LIMIT_WINDOW_SECONDS,
                    )
                ),
            ),
            magic_link_default_tags=default_tags,
            magic_link_default_modules=default_modules,
            session_ttl_seconds=max(
                60, int(raw.get("session_ttl_seconds", DEFAULT_SESSION_TTL_SECONDS))
            ),
            session_renewal_threshold_seconds=max(
                0,
                int(
                    raw.get(
                        "session_renewal_threshold_seconds",
                        DEFAULT_SESSION_RENEWAL_THRESHOLD_SECONDS,
                    )
                ),
            ),
            session_cookie_name=str(raw.get("session_cookie_name", "patzilla_session")).strip()
            or "patzilla_session",
            session_cookie_secure=asbool(raw.get("session_cookie_secure", False)),
            session_cookie_samesite=samesite,
            public_base_url=str(raw.get("public_base_url", "")).strip().rstrip("/"),
            log_magic_link_in_dev=asbool(raw.get("log_magic_link_in_dev", True)),
        )

    @classmethod
    def from_registry(cls, registry: Any) -> AuthSettings:
        """
        Extract `[auth]` settings from a Pyramid application registry.
        """
        app_settings = getattr(registry, "application_settings", None)
        if isinstance(app_settings, Mapping) and "auth" in app_settings:
            return cls.from_mapping(app_settings.get("auth"))

        pyramid_settings = getattr(registry, "settings", None)
        if isinstance(pyramid_settings, Mapping):
            auth_prefixed = {
                key.removeprefix("auth."): value
                for key, value in pyramid_settings.items()
                if isinstance(key, str) and key.startswith("auth.")
            }
            if auth_prefixed:
                return cls.from_mapping(auth_prefixed)

        return cls()
