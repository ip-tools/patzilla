# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
from pyramid.settings import asbool         # Keep this for h.asbool()
from pyramid.threadlocal import get_current_request, get_current_registry
from patzilla.navigator.settings import JavascriptParameterFiddler


# Used for fiddling configuration setting parameters from Python scope to Javascript scope
def configuration_fiddler():
    request = get_current_request()
    fiddler = JavascriptParameterFiddler('navigatorConfiguration', request.runtime_settings)
    return fiddler

# Whether we are in development or production mode
def development_mode():
    registry = get_current_registry()
    try:
        return asbool(registry.application_settings.ip_navigator.development_mode)
    except:
        return False
