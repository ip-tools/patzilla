# -*- coding: utf-8 -*-
# (c) 2026 Andreas Motl <andreas.motl@ip-tools.org>
import dataclasses
import logging
import os
import typing as t

from patzilla.access import create_pools, resolve_client
from patzilla.navigator.settings import GlobalSettings
from patzilla.util.web.identity.store import UserMetricsManager
from patzilla.web.settings import WebSettings

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AppState:
    """
    Application-wide objects, created once at startup, available as `app.state.patzilla`.
    """

    settings: WebSettings
    global_settings: GlobalSettings
    signer: t.Any
    metrics: UserMetricsManager
    pools: t.Dict[str, t.Any]
    templates: t.Any = None

    # Configuration settings, also read by `AuthSettings.from_registry`.
    @property
    def application_settings(self):
        return self.global_settings.application_settings

    @property
    def datasource_settings(self):
        return self.global_settings.datasource_settings

    @property
    def vendor_settings(self):
        return self.global_settings.vendor_settings

    def client(self, datasource, user=None, vendor=None):
        """Return the upstream client for a data source, or `None` when not available."""
        return resolve_client(self.pools, datasource, self.datasource_settings, user=user, vendor=vendor)


def build_state(settings: WebSettings) -> AppState:
    from patzilla.navigator.opaquelinks import create_signer
    from patzilla.util.web.identity.store import provision_users, setup_mongoengine

    global_settings = GlobalSettings(str(settings.configfile))
    metrics = UserMetricsManager()
    state = AppState(
        settings=settings,
        global_settings=global_settings,
        signer=create_signer(),
        metrics=metrics,
        pools=create_pools(global_settings, metrics_manager=metrics),
    )

    if settings.flavor == "web":
        from patzilla.boot.cache import configure_cache_regions
        from patzilla.util.database.beaker_mongodb_gridfs import patch_gridfs_backend
        from patzilla.web.templating import MakoTemplates

        configure_cache_regions(settings.app)
        patch_gridfs_backend()
        setup_mongoengine(settings.mongodb_uri)
        provision_users()
        state.templates = MakoTemplates(reload=settings.reload_templates)

    return state


def static_directory() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "navigator", "static")
