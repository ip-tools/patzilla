# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import json
import logging
from pyramid.settings import asbool
from pyramid.threadlocal import get_current_request

log = logging.getLogger(__name__)

class BackboneModelParameterFiddler(object):

    def __init__(self, name):
        self.name = name

    def settings(self):
        """define default settings"""

        request = get_current_request()

        data = {
            'app.software.version': request.registry.settings.get('SOFTWARE_VERSION', ''),
            'ui.version': 'Software release: ' + request.registry.settings.get('SOFTWARE_VERSION', ''),
            'ui.page.title': 'Patent search',
            'ui.page.subtitle': '',
            'ui.page.footer': 'Data sources: EPO/OPS, DPMA/DEPATISnet, USPTO/PATIMG',
            'ui.productname': 'elmyra <i class="circle-icon">IP</i> suite',
        }

        # prefix settings in confiuration model
        realdata = {}
        for key, value in data.iteritems():
            key = 'setting.' + key
            realdata[key] = value
        return realdata

    def compute_parameters(self):
        """all parameter lifting in one place"""

        request = get_current_request()

        setting_params = dict(self.settings())
        request_params = dict(request.params)
        request_opaque = dict(request.opaque)

        # parameter firewall
        # 1. don't allow "query" from outside on viewer-only domains
        query_allowed = request.headers.get('Host') != 'patentview.elmyra.de'
        if request_params.has_key('query') and not query_allowed:
            log.warn('parameter "query=%s" not allowed on this instance, deleting it', request_params['query'])
            del request_params['query']

        # merge parameters
        # 1. use "settings" as foundation
        # 2. merge "request parameters"
        # 3. merge "opaque parameters" taking the highest precedence
        params = setting_params
        params.update(request_params)
        params.update(request_opaque)

        # backward-compat amendments
        for key, value in params.iteritems():
            if key.startswith('ship_'):
                newkey = key.replace('ship_', 'ship-')
                params[newkey] = value
                del params[key]

        return params

    def render(self):
        """transfer parameters to Backbone model"""
        parameters = self.compute_parameters()
        javascript = self.name + '.set(' + json.dumps(parameters) + ');\n'
        return javascript

fiddler = BackboneModelParameterFiddler('ipsuiteNavigatorConfig')
