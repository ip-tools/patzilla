# -*- coding: utf-8 -*-
# (c) 2013-2022 Andreas Motl <andreas.motl@ip-tools.org>
from patzilla.navigator.settings import RuntimeSettings


def includeme(config):
    config.add_subscriber(runtime_config, "pyramid.events.ContextFound")


def runtime_config(event):
    """
    Provide the runtime settings and attach them to the `request` object.
    """
    event.request.runtime_settings = RuntimeSettings()
