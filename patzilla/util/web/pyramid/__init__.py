# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG

# this is a namespace package
from pkgutil import extend_path
from patzilla.util.web.pyramid.renderer import json_pretty_renderer

__path__ = extend_path(__path__, __name__)

def includeme(config):
    config.add_renderer('prettyjson', json_pretty_renderer)
