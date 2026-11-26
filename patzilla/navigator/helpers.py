# -*- coding: utf-8 -*-
# (c) 2014-2026 Andreas Motl <andreas.motl@ip-tools.org>
from patzilla.navigator.settings import JavascriptParameterFiddler
from patzilla.util.config import asbool


class TemplateHelpers:
    """
    Helper functions available as `h` within templates, bound to the runtime settings of the request.
    """

    asbool = staticmethod(asbool)

    def __init__(self, runtime_settings):
        self.runtime_settings = runtime_settings

    def configuration_fiddler(self):
        """Transfer configuration settings from Python scope to Javascript scope."""
        return JavascriptParameterFiddler('navigatorConfiguration', self.runtime_settings)

    def development_mode(self):
        return self.runtime_settings.development_mode
