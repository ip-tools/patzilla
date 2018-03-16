# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import json
import logging
from pyramid.exceptions import ConfigurationError
from pyramid.threadlocal import get_current_request, get_current_registry
from patzilla.navigator.util import dict_prefix_key, dict_merge
from patzilla.util.config import read_config, read_list, asbool
from patzilla.util.date import datetime_isoformat, unixtime_to_datetime
from patzilla.util.python import _exception_traceback
from patzilla.util.data.container import SmartBunch

log = logging.getLogger(__name__)


class GlobalSettings(object):

    def __init__(self):
        self.registry = get_current_registry()
        self.configfile = self.registry.settings['CONFIG_FILE']
        self.application_settings = self.get_application_settings()
        self.datasource_settings  = self.get_datasource_settings()
        self.vendor_settings      = self.get_vendor_settings()

    def get_application_settings(self):
        # Read configuration file to get global settings
        # TODO: Optimize: Only read once, not on each request!
        return read_config(self.configfile, kind=SmartBunch)

    def get_datasource_settings(self):

        # Container for datasource settings
        datasource_settings = SmartBunch({
            'datasources': [],
            'datasource': SmartBunch(),
            'total': SmartBunch.bunchify({'fulltext_countries': [], 'details_countries': []}),
            })

        # Read datasource settings from configuration
        datasource_settings.datasources = read_list(self.application_settings.get('ip_navigator', {}).get('datasources'))
        datasource_settings.protected_fields = read_list(self.application_settings.get('ip_navigator', {}).get('datasources_protected_fields'))
        for datasource in datasource_settings.datasources:
            settings_key = 'datasource_{name}'.format(name=datasource)
            datasource_info = self.application_settings.get(settings_key, {})
            datasource_info['fulltext_enabled'] = asbool(datasource_info.get('fulltext_enabled', False))
            datasource_info['fulltext_countries'] = read_list(datasource_info.get('fulltext_countries', ''))
            datasource_info['details_enabled'] = asbool(datasource_info.get('details_enabled', False))
            datasource_info['details_countries'] = read_list(datasource_info.get('details_countries', ''))
            datasource_settings.datasource[datasource] = SmartBunch.bunchify(datasource_info)

            # Aggregate data for all countries
            datasource_settings.total.fulltext_countries += datasource_info['fulltext_countries']

        return datasource_settings

    def get_vendor_settings(self):

        # Container for vendor settings
        vendor_settings = SmartBunch({
            'vendors': [],
            'vendor': SmartBunch(),
        })

        # Read vendor settings from configuration
        try:
            vendor_settings.vendors = read_list(self.application_settings.ip_navigator.vendors)
            assert vendor_settings.vendors
        except:
            raise ConfigurationError('No vendor configured in "{configfile}"'.format(configfile=self.configfile))

        for vendor in vendor_settings.vendors:

            settings_key = 'vendor_{name}'.format(name=vendor)
            if settings_key not in self.application_settings:
                raise ConfigurationError('Vendor "{vendor}" not configured in "{configfile}"'.format(
                    vendor=vendor, configfile=self.configfile))

            vendor_info = self.application_settings.get(settings_key, {})
            for key, value in vendor_info.iteritems():
                vendor_info[key] = value.decode('utf-8')

            if 'hostname_matches' in vendor_info:
                vendor_info.hostname_matches = read_list(vendor_info.hostname_matches)

            vendor_settings.vendor[vendor] = SmartBunch.bunchify(vendor_info)

        return vendor_settings


class RuntimeSettings(object):
    """
    All runtime parameters in one single place
    """

    # TODO: Refactor IpsuiteNavigatorConfig.defaults here as well, trim down config.js

    development_hosts = [
        'localhost',
        'offgrid',
    ]

    staging_hosts = [
        'localhost',
        'offgrid',
        'patentsearch-develop.elmyra.de',
        'patentsearch-staging.elmyra.de',
    ]

    def __init__(self):

        self.request = get_current_request()
        self.registry = get_current_registry()

        self.hostname = self.request.host.split(':')[0]

        self.config = self.config_parameters()
        self.theme = self.theme_parameters()
        self.beta_badge = '<div class="label label-success label-large do-not-print">BETA</div>'

    def asdict(self):
        return self.__dict__.copy()

    def environment(self):
        """create default environment"""

        data = {
            'host_name': self.hostname,
            'host': self.request.host,
            'host_port': self.request.host_port,
            'host_url': self.request.host_url,
            'path': self.request.path,
            'path_url': self.request.path_url,
        }

        return data

    def config_settings(self):
        """define default settings"""

        data = {
            'app.software.version': self.registry.settings.get('SOFTWARE_VERSION', ''),
        }

        return data

    def resolve_vendor_settings(self):
        """
        The selection process will use the first configured vendor as default,
        after that it will search through the other configured vendors and will
        select the one which matches the "hostname_matches" pattern
        on a first come, first serve basis.
        """

        # Select vendor by matching hostnames
        vendor_names = self.registry.vendor_settings.vendors
        for vendor_name in vendor_names:
            vendor_info = self.registry.vendor_settings.vendor[vendor_name]
            if 'hostname_matches' in vendor_info:
                for hostname_candidate in vendor_info.hostname_matches:
                    if hostname_candidate in self.hostname:
                        return vendor_info

        # Use first configured vendor as fallback
        vendor_name = self.registry.vendor_settings.vendors[0]
        vendor_info = self.registry.vendor_settings.vendor[vendor_name]
        return vendor_info

    def theme_settings(self):
        """define default settings"""

        data_source_list = [
            '<a href="https://ops.epo.org/" target="_blank" class="incognito pointer">EPO/OPS</a>',
            '<a href="https://depatisnet.dpma.de" target="_blank" class="incognito pointer">DPMA/DEPATISnet</a>',
            '<a href="https://www.uspto.gov/" target="_blank" class="incognito pointer">USPTO/PATIMG</a>',
            '<a href="http://cipo.gc.ca" target="_blank" class="incognito pointer">CIPO</a>',
            '<a href="https://www.ificlaims.com/" target="_blank" class="incognito pointer">IFI Claims</a>',
            '<a href="https://depa.tech/" target="_blank" class="incognito pointer">MTC depa.tech</a>',
        ]

        software_version_label = 'Software release: ' + self.registry.settings.get('SOFTWARE_VERSION', '')
        software_version_link  = '<a href="https://github.com/ip-tools/ip-navigator" target="_blank" ' \
                                 'class="incognito pointer">{label}</a>'.format(label=software_version_label)

        vendor = self.resolve_vendor_settings()
        data = {
            'ui.vendor.name': vendor.organization,
            'ui.vendor.copyright': vendor.copyright_html,
            'ui.productname': vendor.productname,
            'ui.productname.rich': vendor.productname_html,
            'ui.productname.html': vendor.productname_html,
            'ui.productname.login': 'productname_login' in vendor and vendor.productname_login or vendor.productname_html,
            'ui.email.purchase': vendor.email_purchase,
            'ui.email.support': vendor.email_support,

            'ui.version': software_version_link,
            'ui.page.title': vendor.get('page_title', ''), # + ' &nbsp; ' + self.beta_badge,
            'ui.page.subtitle': '',
            'ui.page.footer': 'Data sources: ' + u', '.join(data_source_list),
        }

        if 'stylesheet_uri' in vendor and vendor.stylesheet_uri:
            data['ui.stylesheet'] = vendor.stylesheet_uri

        return data

    def datasource_settings(self):
        """
        Return datasource settings while accounting for sensible settings like API URI and credentials.
        """
        request = get_current_request()
        datasource_settings = SmartBunch.bunchify(request.registry.datasource_settings)
        if 'protected_fields' in datasource_settings:
            for fieldname in datasource_settings.protected_fields:
                for name, settings in datasource_settings.datasource.iteritems():
                    if fieldname in settings:
                        del settings[fieldname]
            del datasource_settings['protected_fields']
        return datasource_settings

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
        isviewer = 'patentview' in host or 'viewer' in host

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
        params['system'] = self.datasource_settings()
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

        # 1. On patentview domains, limit access to liveview mode only
        params['isviewer'] = isviewer
        if isviewer:
            params['mode'] = 'liveview'

        # 2. Compute whether data sources are enabled
        params['google_enabled']    = self.is_datasource_enabled('google')
        params['ifi_enabled']       = self.is_datasource_enabled('ificlaims')
        params['depatech_enabled']  = self.is_datasource_enabled('depatech')


        # E. backward-compat amendments
        for key, value in params.iteritems():
            if key.startswith('ship_'):
                newkey = key.replace('ship_', 'ship-')
                params[newkey] = value
                del params[key]

        return params

    def is_datasource_enabled(self, datasource):

        # Compatibility aliasing
        datasource_user_module = datasource
        if datasource == 'ificlaims':
            datasource_user_module = 'ifi'

        # Matching
        enabled = \
            datasource in self.registry.datasource_settings.datasources and \
            (self.hostname in self.development_hosts or \
             datasource in self.request.user.modules or \
             datasource_user_module in self.request.user.modules)

        return enabled

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


class JavascriptParameterFiddler(object):

    def __init__(self, name, runtime_settings):
        self.name = name
        self.runtime_settings = runtime_settings

    def render(self):
        """
        Transfer runtime settings to Javascript
        """

        # Serialize parameters to json
        # Merge hidden request parameters, e.g. "database=" gets stripped away from site.mako to avoid referrer spam
        # Push current configuration state to browser history
        tplvars = self.runtime_settings.asdict()
        tplvars['config'] = json.dumps(tplvars['config'])
        tplvars['theme']  = json.dumps(tplvars['theme'])
        javascript_config = 'var navigator_configuration = {config};'.format(**tplvars)
        javascript_theme  = 'var navigator_theme = {theme};'.format(**tplvars)
        payload = '\n'.join([javascript_config, javascript_theme])
        return payload
