# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import os
import json
import logging
from copy import deepcopy
from email.utils import parseaddr

from pyramid.exceptions import ConfigurationError
from pyramid.threadlocal import get_current_request, get_current_registry

from patzilla.version import __version__
from patzilla.navigator.util import dict_prefix_key
from patzilla.util.config import read_list, asbool, get_configuration
from patzilla.util.date import datetime_isoformat, unixtime_to_datetime
from patzilla.util.python import _exception_traceback
from patzilla.util.data.container import SmartBunch

log = logging.getLogger(__name__)


class GlobalSettings(object):

    def __init__(self, configfile):
        self.configfile = self.get_configuration_file(configfile)
        self.application_settings = self.get_application_settings()
        self.datasource_settings  = self.get_datasource_settings()
        self.vendor_settings      = self.get_vendor_settings()

        # Debugging
        #print self.datasource_settings.prettify()
        #print self.vendor_settings.prettify()

    @classmethod
    def get_configuration_file(cls, configfile=None):

        # Compute configuration file
        if not configfile:
            configfile = os.environ.get('PATZILLA_CONFIG')

        if not configfile:
            raise ValueError('No configuration file, either use --config=/path/to/patzilla.ini or set PATZILLA_CONFIG environment variable')

        log.info('Root configuration file is {}'.format(configfile))
        return configfile

    def get_application_settings(self):
        """
        Read configuration file to get global settings
        """

        # TODO: Optimize: Only read once, not on each request!
        settings = get_configuration(self.configfile, kind=SmartBunch)

        # Add some global settings
        settings['software_version'] = __version__

        # Amend settings: Make real Booleans from strings
        settings['smtp']['tls'] = asbool(settings['smtp'].get('tls', True))

        return settings

    def get_datasource_settings(self, vendor=None):

        # Container for datasource settings.
        datasource_settings = SmartBunch({
            'datasources': [],
            'datasource': SmartBunch(),
            'total': SmartBunch.bunchify({'fulltext_countries': [], 'details_countries': []}),
        })

        # Read datasource settings from configuration.
        datasource_settings.datasources = read_list(self.application_settings.get('ip_navigator', {}).get('datasources'))
        datasource_settings.protected_fields = read_list(self.application_settings.get('ip_navigator', {}).get('datasources_protected_fields'))

        for datasource in datasource_settings.datasources:
            datasource_info = SmartBunch()
            if vendor is None:
                settings_key = 'datasource:{name}'.format(name=datasource)
            else:
                settings_key = 'datasource:{name}:{vendor}'.format(name=datasource, vendor=vendor)

            ds_settings = self.application_settings.get(settings_key, {})
            for key, value in ds_settings.iteritems():
                datasource_info.setdefault(key, value)
            datasource_info.setdefault('fulltext_enabled', asbool(ds_settings.get('fulltext_enabled', False)))
            datasource_info.setdefault('fulltext_countries', read_list(ds_settings.get('fulltext_countries', '')))
            datasource_info.setdefault('details_enabled', asbool(ds_settings.get('details_enabled', False)))
            datasource_info.setdefault('details_countries', read_list(ds_settings.get('details_countries', '')))

            datasource_settings.datasource[datasource] = SmartBunch.bunchify(datasource_info)

            # Aggregate data for all countries.
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

            settings_key = 'vendor:{name}'.format(name=vendor)
            if settings_key not in self.application_settings:
                raise ConfigurationError('Vendor "{vendor}" not configured in "{configfile}"'.format(
                    vendor=vendor, configfile=self.configfile))

            vendor_info = self.application_settings.get(settings_key, {})
            for key, value in vendor_info.iteritems():
                vendor_info[key] = value.decode('utf-8')

            if 'hostname_matches' in vendor_info:
                vendor_info.hostname_matches = read_list(vendor_info.hostname_matches)

            # Per-vendor email configuration.
            vendor_info.email = self.get_email_settings(vendor)

            # Per-vendor data source settings.
            vendor_info.datasource_settings = self.get_datasource_settings(vendor)

            # Collect all vendor settings.
            vendor_settings.vendor[vendor] = SmartBunch.bunchify(vendor_info)

        return vendor_settings

    def get_email_settings(self, vendor):
        """
        Read default/global email settings and
        update with per-vendor email settings.
        """

        # Container for email settings
        email_settings = SmartBunch({
            'addressbook': [],
            'content': SmartBunch(),
        })

        for setting_name in ['addressbook', 'content']:
            setting_key = 'email_{}'.format(setting_name)
            defaults = self.application_settings.get(setting_key)
            specific = self.application_settings.get(setting_key + ':' + vendor)

            thing = deepcopy(defaults)
            if defaults and specific:
                thing.update(deepcopy(specific))

            for key, value in thing.items():
                thing[key] = value.decode('utf-8')

            email_settings[setting_name] = thing

        return email_settings


class RuntimeSettings(object):
    """
    All runtime parameters in one single place
    """

    # TODO: Refactor IpsuiteNavigatorConfig.defaults here as well, trim down config.js

    def __init__(self):

        self.request = get_current_request()
        self.registry = get_current_registry()

        self.hostname = self.request.host.split(':')[0]
        self.development_mode = development_mode()

        self.vendor = self.effective_vendor()
        self.config = self.config_parameters()
        self.theme = self.theme_parameters()
        self.beta_badge = '<span class="label label-success label-large do-not-print">BETA</span>'

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
            'app.software.version': self.registry.application_settings.software_version,
        }

        return data

    def effective_vendor(self):
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
            vendor_info['name'] = vendor_name
            if 'hostname_matches' in vendor_info:
                for hostname_candidate in vendor_info.hostname_matches:
                    if hostname_candidate in self.hostname:
                        return vendor_info

        # If now vendor can be resolved, use first configured vendor as fallback
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
            '<a href="https://www.ificlaims.com/" target="_blank" class="incognito pointer">IFI CLAIMS</a>',
            '<a href="https://depa.tech/" target="_blank" class="incognito pointer">MTC depa.tech</a>',
            #'<a href="https://patentfamily.com/" target="_blank" class="incognito pointer">SIP</a>',
        ]

        software_version_label = 'PatZilla release: ' + self.registry.application_settings.software_version
        software_version_link  = '<a href="https://github.com/ip-tools/ip-navigator" target="_blank" ' \
                                 'class="incognito pointer">{label}</a>'.format(label=software_version_label)

        vendor = self.vendor

        # Format email addresses
        email_support = parseaddr(vendor.email.addressbook.support)[1]
        email_purchase = parseaddr(vendor.email.addressbook.purchase)[1]

        data = {
            'ui.vendor.name': vendor.organization,
            'ui.vendor.copyright': vendor.copyright_html,
            'ui.productname': vendor.productname,
            'ui.productname.rich': vendor.productname_html,
            'ui.productname.html': vendor.productname_html,
            'ui.productname.login': 'productname_login' in vendor and vendor.productname_login or vendor.productname_html,
            'ui.email.support': email_support,
            'ui.email.purchase': email_purchase,

            'ui.version': software_version_link,
            'ui.page.title': vendor.get('page_title', ''), # + ' &nbsp; ' + self.beta_badge,
            'ui.page.subtitle': '',
            'ui.page.footer': 'Data sources: ' + u', '.join(data_source_list),
        }

        # Transfer all properties having designated prefixes 1:1
        prefixes = ['ui.', 'feature.']
        for key, value in vendor.iteritems():
            for prefix in prefixes:
                if key.startswith(prefix):
                    if key.endswith('.enabled'):
                        value = asbool(value)
                    data[key] = value

        # Backward compatibility
        if 'ui.stylesheet' not in data:
            data['ui.stylesheet'] = vendor.get('stylesheet_uri')

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
        isviewer = 'patentview' in host or 'viewer' in host or 'patview' in host

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

        # 0. Vendor
        params['vendor'] = self.vendor.name

        # 1. On patentview domains, limit access to liveview mode only
        params['isviewer'] = isviewer
        if isviewer:
            params['mode'] = 'liveview'

        # 2. Compute whether data sources are enabled
        params['datasources_enabled'] = []
        for datasource in self.registry.datasource_settings.datasources:
            if self.is_datasource_enabled(datasource):
                params['datasources_enabled'].append(datasource)

        # E. backward-compat amendments
        for key, value in params.iteritems():
            if key.startswith('ship_'):
                newkey = key.replace('ship_', 'ship-')
                params[newkey] = value
                del params[key]

        return params

    def is_datasource_enabled(self, datasource):

        # Default data sources are always enabled
        if datasource in ['ops', 'depatisnet']:
            return True

        # Compatibility aliasing
        datasource_user_module = datasource
        if datasource == 'ificlaims':
            datasource_user_module = 'ifi'

        # Debugging: Emulate specific conditions
        #self.development_mode = False

        # Matching
        enabled = \
            datasource in self.registry.datasource_settings.datasources and \
            (self.development_mode or \
             datasource in self.request.user.modules or \
             datasource_user_module in self.request.user.modules)

        return enabled

    def theme_parameters(self):
        request = get_current_request()

        params = self.theme_settings()

        # 3. add badges for staging- and development-environments
        badge_text = None
        label_kind = None
        if 'localhost' in self.hostname or '127.0.0.' in self.hostname:
            badge_text = 'localhost'
            label_kind = 'info'
        elif 'develop' in self.hostname:
            badge_text = 'development'
            label_kind = 'info'
        elif 'staging' in self.hostname:
            badge_text = 'staging'
            label_kind = 'info'

        if badge_text and label_kind:
            params['ui.environment.badge'] = \
                '<span class="label label-{label_kind} label-large do-not-print">{badge_text}</span>'.format(**locals())

        # TODO: Move the html stuff elsewhere!
        if self.config.get('mode') == 'liveview':
            params['ui.page.title'] = 'Patent view'
            params['ui.spinner'] = ' &nbsp; <i class="spinner icon-refresh icon-spin" style="display: none"></i>'
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


# Whether we are in development or production mode
def development_mode():
    registry = get_current_registry()
    try:
        return asbool(registry.application_settings.ip_navigator.development_mode)
    except:
        return False
