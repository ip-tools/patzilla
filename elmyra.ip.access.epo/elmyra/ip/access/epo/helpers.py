# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import json
import logging
from pprint import pprint
from elmyra.ip.access.epo.util import dict_prefix_key, dict_merge
from elmyra.ip.util.config import read_config, read_list
from elmyra.ip.util.data.container import SmartBunch
from elmyra.ip.util.date import datetime_isoformat, unixtime_to_datetime
from elmyra.ip.util.python import _exception_traceback
from pyramid.settings import asbool     # Required by template, don't remove!
from pyramid.threadlocal import get_current_request

log = logging.getLogger(__name__)

class Bootstrapper(object):
    """all parameter fiddling in one single place :-)"""

    # TODO: refactor this out of helpers.py, just import here
    # TODO: refactor IpsuiteNavigatorConfig.defaults here as well, trim down config.js

    staging_hosts = [
        'localhost',
        'offgrid',
        'patentsearch-develop.elmyra.de',
        'patentsearch-staging.elmyra.de',
        ]

    def __init__(self):
        self.config = self.config_parameters()
        self.theme = self.theme_parameters()
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

    def config_settings(self):
        """define default settings"""

        request = get_current_request()

        data = {
            'app.software.version': request.registry.settings.get('SOFTWARE_VERSION', ''),
        }

        return data

    def theme_settings(self):
        """define default settings"""

        request = get_current_request()

        data = {
            'ui.vendor.name': 'Elmyra',
            'ui.vendor.copyright': u'&copy; 2013-2017, <a href="https://www.elmyra.de/" class="incognito" target="_blank">Elmyra UG</a> — All rights reserved.',
            'ui.productname': 'Elmyra IP Navigator',
            'ui.productname.rich': '<span class="header-logo">Elmyra <i class="circle-icon">IP</i> Navigator</span>',
            'ui.email.purchase': 'purchase@elmyra.de',
            'ui.email.support': 'purchase@elmyra.de',

            'ui.version': 'Software release: ' + request.registry.settings.get('SOFTWARE_VERSION', ''),
            'ui.page.title': 'Patent search', # + ' &nbsp; ' + self.beta_badge,
            'ui.page.subtitle': '',
            'ui.page.footer': 'Data sources: EPO/OPS, DPMA/DEPATISnet, USPTO/PATIMG, CIPO, <a target="_blank" class="incognito pointer action-help-ificlaims">IFI Claims</a>',

            'ui.css': {
                # Page header background
                '.header-container': {
                    'background-image': 'url(/static/img/header-small.jpg)',
                },
                '.header-inner-left': {
                    'margin-top': '8px',
                },
                '.header-inner-right': {
                    'margin-top': '10px',
                },

                '.header-logo': {
                    'font-size': '24.5px',
                    'line-height': '40px',
                    'font-weight': 'bold',
                },

            }
        }

        if self.hostname == 'patentview.ip-tools.io':
            dict_merge(data, {
                'ui.productname': 'Patent View',
                'ui.productname.rich': '',
            })

        if 'patoffice-navigator' in self.hostname or \
            self.hostname.endswith('.europatent.net') or \
            self.hostname.endswith('.patoffice.de'):
            vendor_color = 'rgba(96, 125, 139, 0.4)'
            dict_merge(data, {
                'ui.productname': 'PATOffice Navigator',
                'ui.productname.rich': '<span class="header-logo">PATOffice Navigator</span> <img width="130" src="/static/vendor/europatent/europatent_logo.png"/>',
                'ui.header.background_image': None,
                'ui.page.title': '',
                'ui.css': {

                    # Header styles
                    '.header-container': {

                        # Page header background
                        'background-image': None,

                        #'background-color': vendor_color,
                        'padding-bottom': '10px',
                        'border-bottom': '1px solid #aaaaaa',

                        'margin-bottom': '0px',

                        # http://www.cssmatic.com/box-shadow
                        #'-webkit-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        #'-moz-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        #'box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        },

                    '.header-inner-left': {
                        'margin-top': '35px',
                    },

                    '.header-logo': {
                        'font-size': '3em',
                        'font-weight': 500,
                        #'font-variant': 'small-caps',
                        'letter-spacing': '0.05em',
                        'color': '#333',
                        'margin-right': '0.6em',
                        },

                    }
            })

        if 'inav-web' in self.hostname:
            vendor_color = '#7ec622'
            dict_merge(data, {
                'ui.productname': ' FulltextPRONavigator',
                'ui.productname.rich': '<div class="header-logo">Navigator</div> <img width="400" src="/static/vendor/ftpro/ftpro_logo.png"/>',
                'ui.header.background_image': None,
                'ui.page.title': '',
                'ui.css': {

                    # Header styles
                    '.header-container': {

                        # Page header background
                        'background-image': None,
                        'background-color': vendor_color,
                        'margin-bottom': '20px',

                        # http://www.cssmatic.com/box-shadow
                        '-webkit-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        '-moz-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        'box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        },

                    '.header-inner-left': {
                        'margin-top': '25px',
                        },

                    '.header-logo': {
                        #'font-family': 'Arial Black',
                        'font-size': '3em',
                        'font-weight': 500,
                        #'font-variant': 'small-caps',
                        'letter-spacing': '0.05em',
                        'color': '#fff',
                        'margin-right': '0.6em',
                        'line-height': '50px',
                        },

                    }
            })

        if 'patselect' in self.hostname:
            vendor_color = 'rgba(54,127,179,0.71)'
            dict_merge(data, {
                'ui.productname': 'SERVIVA Patselect Navigator',
                'ui.productname.rich': '<span class="header-logo">Patselect Navigator</span> <img src="/static/vendor/serviva/serviva_logo.png"/>',
                'ui.header.background_image': None,
                'ui.page.title': '',
                'ui.css': {

                    # Header styles
                    '.header-container': {

                        # Page header background
                        'background-image': None,
                        'background-color': vendor_color,
                        'margin-bottom': '20px',

                        # http://www.cssmatic.com/box-shadow
                        '-webkit-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        '-moz-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        'box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                    },

                    '.header-inner-left': {
                        'margin-top': '25px',
                    },

                    '.header-logo': {
                        'font-size': '3em',
                        'font-weight': 500,
                        'font-variant': 'small-caps',
                        'letter-spacing': '0.05em',
                        'color': '#333',
                        'margin-right': '0.8em',
                    },

                }
            })

        if 'sheldon' in self.hostname:
            vendor_color = 'rgba(128,84,120,0.8)'
            dict_merge(data, {
                'ui.productname': 'MTC Sheldon Search',
                'ui.productname.rich': '<span class="header-logo">Sheldon Search</span> <img width="130" src="/static/vendor/mtc/mtc_logo.png"/>',
                'ui.header.background_image': None,
                'ui.page.title': '',
                'ui.css': {

                    # Header styles
                    '.header-container': {

                        # Page header background
                        'background-image': None,
                        'background-color': vendor_color,
                        'margin-bottom': '20px',

                        # http://www.cssmatic.com/box-shadow
                        '-webkit-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        '-moz-box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        'box-shadow': '0px 10px 7px 3px {color}'.format(color=vendor_color),
                        },

                    '.header-inner-left': {
                        'margin-top': '15px',
                        },
                    '.header-inner-right': {
                        'margin-top': '15px',
                        },

                    '.header-logo': {
                        'font-family': 'Playfair Display',
                        'font-size': '3em',
                        'font-weight': '500',
                        #'font-style': 'italic',
                        'font-variant': 'small-caps',
                        'letter-spacing': '0.05em',
                        'color': '#333',
                        'margin-right': '0.6em',
                        },

                    }
            })

        return data

    def system_settings(self):

        request = get_current_request()
        pyramid_settings = request.registry.settings

        # Read configuration file to get global settings
        # TODO: Optimize: Only read once, not on each request!
        # See also email:submit.py
        all_settings = read_config(pyramid_settings['CONFIG_FILE'])

        # Define baseline of system settings
        system_settings = SmartBunch({
            'datasources': [],
            'datasource': SmartBunch(),
            'total': SmartBunch.bunchify({'fulltext_countries': []}),
        })

        # Read system settings from configuration
        system_settings.datasources = read_list(all_settings.get('ip_navigator', {}).get('datasources'))
        for datasource in system_settings.datasources:
            datasource_setting_key = 'datasource_{name}'.format(name=datasource)
            datasource_settings = all_settings.get(datasource_setting_key, {})
            datasource_settings['fulltext_countries'] = read_list(datasource_settings.get('fulltext_countries', ''))
            datasource_settings['fulltext_enabled'] = asbool(datasource_settings.get('fulltext_enabled', False))
            system_settings.datasource[datasource] = SmartBunch.bunchify(datasource_settings)

            # Aggregate data for all countries
            system_settings.total.fulltext_countries += datasource_settings['fulltext_countries']

        #print 'system_settings:\n', system_settings

        return system_settings

    def config_parameters(self):

        request = get_current_request()

        # prefix environment and settings in configuration model
        environment = dict_prefix_key(self.environment(), 'request.')
        setting_params = dict_prefix_key(self.config_settings(), 'setting.')
        request_params = dict(request.params)
        user_params = {}
        if request.user:

            # Formulate JS-domain settings
            user_params = dict_prefix_key({
                'modules': request.user.modules,
                'tags': request.user.tags},
                'user.')

            # Get representation of user attributes
            user_dict = json.loads(request.user.to_json())

            # Strip sensitive information
            if '_id' in user_dict:
                del user_dict['_id']
            if 'password' in user_dict:
                del user_dict['password']
            if 'upstream_credentials' in user_dict:
                del user_dict['upstream_credentials']

            # Add whole user attributes to JS-domain
            user_params['user'] = user_dict

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
        params = {}
        params['system'] = self.system_settings()
        params.update(environment)
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

        # 1. on patentview.elmyra.de, only run liveview
        params['isviewer'] = isviewer
        if isviewer:
            params['mode'] = 'liveview'

        # 2.a compute whether datasource "FulltextPRO" is enabled
        user_modules = params.get('user.modules', [])
        self.hostname = params.get('request.host_name')

        ftpro_allowed_hosts = [
            'localhost',
            'offgrid',
        ]
        params['ftpro_enabled'] =\
            self.hostname in ftpro_allowed_hosts or \
            'ftpro' in user_modules

        # 2.b compute whether datasource "Serviva Data Proxy" is enabled
        ificlaims_allowed_hosts = [
            'localhost',
            'offgrid',
            ]
        params['ifi_enabled'] =\
            self.hostname in ificlaims_allowed_hosts or \
            'ifi' in user_modules

        # 2.c compute whether Google datasource is allowed
        #params['google_enabled'] = hostname in self.staging_hosts
        params['google_enabled'] = False


        # E. backward-compat amendments
        for key, value in params.iteritems():
            if key.startswith('ship_'):
                newkey = key.replace('ship_', 'ship-')
                params[newkey] = value
                del params[key]

        return params


    def theme_parameters(self):
        request = get_current_request()

        params = self.theme_settings()

        # 3. add badges for staging- and development-environments
        if self.hostname in self.staging_hosts:
            badge_text = None
            label_kind = None
            if 'staging' in self.hostname:
                badge_text = 'staging'
                label_kind = 'info'
            elif 'develop' in self.hostname:
                badge_text = 'development'
                label_kind = 'info'
            elif 'localhost' in self.hostname:
                badge_text = 'localhost'
                label_kind = 'info'
            elif 'localhost' in self.hostname:
                badge_text = 'localhost'
                label_kind = 'info'
            if badge_text and label_kind:
                params['ui.page.title'] += ' &nbsp; ' + '<div class="label label-{label_kind} label-large do-not-print">{badge_text}</div>'.format(**locals())

        # TODO: Move the html stuff elsewhere!
        if self.config.get('mode') == 'liveview':
            params['ui.page.title'] = 'Patent view'
            #params['ui.page.title'] += ' &nbsp; ' + self.beta_badge
            params['ui.page.title'] += ' &nbsp; <i class="spinner icon-refresh icon-spin" style="display: none"></i>'
            if self.config.get('datasource') == 'review':
                params['ui.page.statusline'] =\
                '<span id="ui-project-name"></span>' +\
                ' <span id="ui-project-dates"></span>'

            link_expires = self.config.get('link_expires')
            if link_expires:
                params.setdefault('ui.page.statusline', '')
                params['ui.page.statusline'] += ' <span id="ui-opaquelink-expiry"></span>'

        return params


class BackboneModelParameterFiddler(object):

    def __init__(self, name):
        self.name = name

    def render(self):
        """transfer parameters to Backbone model"""

        boot = Bootstrapper()

        # serialize parameters to json
        # merge hidden request parameters, e.g. "database=" gets stripped away form site.mako to avoid referrer spam
        # push current configuration state to browser history
        tplvars = boot.__dict__.copy()
        tplvars['parameters_json'] = json.dumps(boot.config)
        javascript_config = """
            {name} = new NavigatorConfiguration();
            {name}.set({parameters_json});
            {name}.set(window.request_hidden);
            if ({name}.get('opaque.meta.status') != 'error') {{
                {name}.history_pushstate();
            }}
        """.format(name=self.name, **tplvars)

        tplvars = {}
        tplvars['parameters_json'] = json.dumps(boot.theme)
        javascript_theme = """
            var theme_settings = {{}};
            _.extend(theme_settings, {{config: navigatorConfiguration}});
            _.extend(theme_settings, {parameters_json});
            navigatorTheme = new NavigatorTheme(theme_settings);
        """.format(**tplvars)

        #print 'javascript_config:', javascript_config

        payload = '\n'.join([javascript_config, javascript_theme])
        return payload

fiddler = BackboneModelParameterFiddler('navigatorConfiguration')
