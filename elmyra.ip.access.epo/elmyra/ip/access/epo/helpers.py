# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import json
import logging
from elmyra.ip.access.epo.util import dict_prefix_key
from elmyra.ip.util.date import unixtime_to_human, datetime_isoformat, unixtime_to_datetime
from elmyra.ip.util.python import _exception_traceback
from pyramid.settings import asbool     # required by template
from pyramid.threadlocal import get_current_request

log = logging.getLogger(__name__)

class BackboneModelParameterFiddler(object):
    """all parameter fiddling in one single place :-)"""

    # TODO: refactor this out of helpers.py, just import here
    # TODO: refactor IpsuiteNavigatorConfig.defaults here as well, trim down config.js

    def __init__(self, name):
        self.name = name
        self.beta_badge = '<div class="label label-success label-large do-not-print">BETA</div>'

    def environment(self):
        """create default environment"""

        request = get_current_request()

        data = {
            'host': request.host,
            'host_name': request.host.split(':')[0],
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
            'ui.page.title': 'Patent search', # + ' &nbsp; ' + self.beta_badge,
            'ui.page.subtitle': '',
            'ui.page.footer': 'Data sources: EPO/OPS, DPMA/DEPATISnet, USPTO/PATIMG, CIPO, FulltextPRO',
            'ui.productname': 'elmyra <i class="circle-icon">IP</i> suite',
        }

        return data

    def compute_parameters(self):

        request = get_current_request()

        # prefix environment and settings in configuration model
        environment = dict_prefix_key(self.environment(), 'request.')
        setting_params = dict_prefix_key(self.settings(), 'setting.')
        request_params = dict(request.params)
        user_params = {}
        if request.user:
            user_params = dict_prefix_key({
                'modules': request.user.modules,
                'tags': request.user.tags,
            }, 'user.')
        request_opaque = dict(request.opaque)
        request_opaque_meta = dict_prefix_key(dict(request.opaque_meta), 'opaque.meta.')

        try:
            unixtime = request.opaque_meta.get('exp')
            if unixtime:
                request_opaque['link_expires'] = datetime_isoformat(unixtime_to_datetime(int(unixtime)))
        except Exception as ex:
            log.error(
                'Could not compute opaque parameter link expiry time, unixtime=%s. '
                'Exception was: %s\n%s', unixtime, ex, _exception_traceback())

        # A. parameter firewall, INPUT

        # determine if we're in view-only mode by matching against the hostname
        host = request.headers.get('Host')
        isviewer = 'patentview' in host

        # 1. don't allow "query" from outside on view-only domains
        if request_params.has_key('query') and isviewer:
            log.warn('parameter "query=%s" not allowed on this vhost, purging it', request_params['query'])
            del request_params['query']


        # B. merge parameters
        # 1. use "environment" as foundation (prefixed "request.")
        # 2. merge "settings" (prefixed "setting.")
        # 3. merge "opaque meta" parameters (prefixed "opaque.meta.")
        # 4. merge "request parameters"
        # 5. merge "user parameters"
        # 6. merge "opaque parameters" taking the highest precedence
        params = environment
        params.update(setting_params)
        params.update(request_opaque_meta)
        params.update(request_params)
        params.update(user_params)
        params.update(request_opaque)


        # C. parameter firewall, OUTPUT

        # remove "opaque parameter"
        if params.has_key('op'):
            del params['op']


        # D. special customizations

        staging_hosts = [
            'localhost',
            'offgrid',
            'patentsearch-develop.elmyra.de',
            'patentsearch-staging.elmyra.de',
        ]

        # 1. on patentview.elmyra.de, only run liveview
        params['isviewer'] = isviewer
        if isviewer:
            params['mode'] = 'liveview'

        # TODO: move the html stuff elsewhere!
        if params.get('mode') == 'liveview':
            params['setting.ui.page.title'] = 'Patent view'
            #params['setting.ui.page.title'] += ' &nbsp; ' + self.beta_badge
            params['setting.ui.page.title'] += ' &nbsp; <i class="spinner icon-refresh icon-spin" style="display: none"></i>'
            if params.get('datasource') == 'review':
                params['setting.ui.page.statusline'] = \
                    '<span id="ui-project-name"></span>' + \
                    ' <span id="ui-project-dates"></span>'

            link_expires = params.get('link_expires')
            if link_expires:
                params.setdefault('setting.ui.page.statusline', '')
                params['setting.ui.page.statusline'] += ' <span id="ui-opaquelink-expiry"></span>'

        # 2.a compute whether datasource "FulltextPRO" is enabled
        user_modules = params.get('user.modules', [])
        hostname = params.get('request.host_name')

        ftpro_allowed_hosts = [
            'localhost',
            'offgrid',
        ]
        params['ftpro_enabled'] = \
            hostname in ftpro_allowed_hosts or \
            'ftpro' in user_modules

        # 2.b compute whether datasource "Serviva Data Proxy" is enabled
        ificlaims_allowed_hosts = [
            'localhost',
            'offgrid',
            ]
        params['ifi_enabled'] = \
            hostname in ificlaims_allowed_hosts or \
            'ifi' in user_modules

        # 2.c compute whether Google datasource is allowed
        params['google_allowed'] = hostname in staging_hosts


        # 3. add badges for staging- and development-environments
        if hostname in staging_hosts:
            badge_text = None
            label_kind = None
            if 'staging' in hostname:
                badge_text = 'staging'
                label_kind = 'info'
            elif 'develop' in hostname:
                badge_text = 'development'
                label_kind = 'info'
            elif 'localhost' in hostname:
                badge_text = 'localhost'
                label_kind = 'info'
            elif 'localhost' in hostname:
                badge_text = 'localhost'
                label_kind = 'info'
            if badge_text and label_kind:
                params['setting.ui.page.title'] += ' &nbsp; ' + '<div class="label label-{label_kind} label-large do-not-print">{badge_text}</div>'.format(**locals())

        # E. backward-compat amendments
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
            if ({name}.get('opaque.meta.status') != 'error') {{
                {name}.history_pushstate();
            }}
        """.format(**tplvars)

        return javascript

fiddler = BackboneModelParameterFiddler('ipsuiteNavigatorConfig')
