# -*- coding: utf-8 -*-
# (c) 2013-2022 Andreas Motl <andreas.motl@ip-tools.org>
from patzilla.navigator.settings import RuntimeSettings


def setup(registry):
    registry.add_request_method(runtime_settings)


def runtime_settings(request):
    """
    Provide the runtime settings as `request.runtime_settings`, computed lazily on first access.
    """
    return RuntimeSettings(request=request)
