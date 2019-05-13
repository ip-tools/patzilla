# -*- coding: utf-8 -*-
# (c) 2014-2019 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import epo_ops
from bunch import bunchify
from pyramid.threadlocal import get_current_registry
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from patzilla.util.web.identity.store import IUserMetricsManager

logger = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_ops_client_pool, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(OpsClientPool())
    config.add_subscriber(attach_ops_client, "pyramid.events.ContextFound")


def attach_ops_client(event):

    # Don't start data source machinery on requests to static assets.
    if '/static' in event.request.url:
        return

    #logger.info('Attaching OPS client to request object')

    request = event.request
    registry = request.registry

    pool = registry.getUtility(IOpsClientPool)

    vendor_settings = request.runtime_settings.vendor

    credentials_source = None

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ops'):
        credentials_source = request.user.userid
        credentials_data = request.user.upstream_credentials['ops']

    # Vendor-wide credentials
    elif vendor_settings and 'datasource_settings' in vendor_settings:
        credentials_source = 'vendor'
        credentials_data = get_ops_credentials(vendor_settings.datasource_settings)

    # Fall back to system-wide credentials
    if not credentials_data:
        credentials_source = 'system'
        credentials_data = get_ops_credentials(registry.datasource_settings)

    logger.info('Attaching OPS credentials from "{}": {}...'.format(credentials_source, credentials_data['consumer_key'][:10]))

    if credentials_data:
        request.ops_client = pool.get(credentials_source, credentials_data)
    else:
        raise KeyError('No credentials for data source "OPS" configured')


def get_ops_credentials(datasource_settings):
    datasources = datasource_settings.datasources
    datasource = datasource_settings.datasource
    if 'ops' in datasources and 'ops' in datasource and 'api_consumer_key' in datasource.ops and 'api_consumer_secret' in datasource.ops:
        system_credentials = bunchify({
            'consumer_key': datasource.ops.api_consumer_key,
            'consumer_secret': datasource.ops.api_consumer_secret,
        })
        return system_credentials


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IOpsClientPool(Interface):
    pass

class OpsClientPool(object):

    implements(IOpsClientPool)

    def __init__(self):
        self.clients = {}
        logger.info('Creating OpsClientPool')

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:

            # TODO: Enable throttling and caching.
            ops = epo_ops.Client(
                key=credentials['consumer_key'], secret=credentials['consumer_secret'],
                accept_type='json', middlewares=[]
            )

            # Attach metrics manager object to ops client instance.
            registry = get_current_registry()
            ops.metrics_manager = registry.getUtility(IUserMetricsManager)
            self.clients[identifier] = ops

        return self.clients.get(identifier)


# Monkeypatch epo_ops_client
def _make_request(self, url, data, extra_headers=None, params=None):
    extra_headers = extra_headers or {}
    token = 'Bearer {0}'.format(self.access_token.token)
    extra_headers['Authorization'] = token

    response = self._post(url, data, extra_headers, params)
    response = self._check_for_expired_token(response)
    response = self._check_for_exceeded_quota(response)

    # Let errors propagate. Don't croak on anything status >= 400.
    #response.raise_for_status()

    return response

epo_ops.Client._make_request = _make_request
