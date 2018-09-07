# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
from pyramid.threadlocal import get_current_request
from patzilla.navigator.settings import JavascriptParameterFiddler
from pyramid.settings import asbool                             # Keep this for h.asbool()
from patzilla.navigator.settings import development_mode        # Keep this for h.development_mode()


# Used for fiddling configuration setting parameters from Python scope to Javascript scope
def configuration_fiddler():
    request = get_current_request()
    fiddler = JavascriptParameterFiddler('navigatorConfiguration', request.runtime_settings)
    return fiddler
