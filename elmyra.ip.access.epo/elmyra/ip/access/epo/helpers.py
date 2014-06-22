# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import json
import logging
from ago import human
from datetime import datetime
from elmyra.ip.access.epo.util import dict_prefix_key
from pyramid.settings import asbool     # required by template
from pyramid.threadlocal import get_current_request

log = logging.getLogger(__name__)

class BackboneModelParameterFiddler(object):
    """all parameter fiddling in one single place :-)"""

    # TODO: refactor IpsuiteNavigatorConfig.defaults here as well, trim down config.js

    def __init__(self, name):
        self.name = name

    def environment(self):
        """create default environment"""

        request = get_current_request()

        data = {
            'host': request.host,
            'host_port': request.host_port,
            'host_url': request.host_url,
            'path': request.path,
            'path_url': request.path_url,
        }

        return data

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

        return data

    def compute_parameters(self):

        request = get_current_request()

        # prefix environment and settings in configuration model
        environment = dict_prefix_key(self.environment(), 'request.')
        setting_params = dict_prefix_key(self.settings(), 'setting.')
        request_params = dict(request.params)
        request_opaque = dict(request.opaque)
        request_opaque['link_expires'] = request.opaque_meta.get('exp')

        # A. parameter firewall, INPUT
        host = request.headers.get('Host')
        isviewer = host in ['patentview.elmyra.de']

        # 1. don't allow "query" from outside on viewer-only domains
        if request_params.has_key('query') and isviewer:
            log.warn('parameter "query=%s" not allowed on this vhost, deleting it', request_params['query'])
            del request_params['query']


        # B. merge parameters
        # 1. use "environment" as foundation
        # 2. merge "settings"
        # 3. merge "request parameters"
        # 4. merge "opaque parameters" taking the highest precedence
        params = environment
        params.update(setting_params)
        params.update(request_params)
        params.update(request_opaque)


        # C. parameter firewall, OUTPUT
        if params.has_key('op'):
            del params['op']


        # D. special customizations

        # 1. on patentview.elmyra.de, only run liveview
        params['isviewer'] = isviewer
        if isviewer:
            params['mode'] = 'liveview'

        if params.get('mode') == 'liveview':
            params['setting.ui.page.title'] = 'Patent view'
            if params.get('datasource') == 'review':
                params['setting.ui.page.subtitle'] = \
                    'Review for project "' + params.get('project', '') + '"' + \
                    ', <span id="ui-project-dates"></span>.'
            link_expires = params.get('link_expires')
            if link_expires is not None:
                link_expires = datetime.fromtimestamp(link_expires)
                params['setting.ui.page.subtitle'] += ' Link expires ' + human(link_expires) + '.';


        # D. backward-compat amendments
        for key, value in params.iteritems():
            if key.startswith('ship_'):
                newkey = key.replace('ship_', 'ship-')
                params[newkey] = value
                del params[key]

        return params

    def render(self):
        """transfer parameters to Backbone model"""

        parameters = self.compute_parameters()

        # serialize parameters to json
        # merge hidden request parameters, e.g. "database=" gets stripped away form site.mako to avoid referrer spam
        # push current configuration state to browser history
        tplvars = self.__dict__.copy()
        tplvars['parameters_json'] = json.dumps(parameters)
        javascript = """
            {name} = new IpsuiteNavigatorConfig();
            {name}.set({parameters_json});
            {name}.set(window.request_hidden);
            {name}.history_pushstate();
        """.format(**tplvars)

        return javascript

fiddler = BackboneModelParameterFiddler('ipsuiteNavigatorConfig')
