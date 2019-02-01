# -*- coding: utf-8 -*-
# (c) 2014-2019 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import epo_ops
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
    #logger.info('Attaching OAuth client to request')

    request = event.request
    registry = request.registry

    pool = registry.getUtility(IOpsClientPool)

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ops'):
        request.ops_client = pool.get(request.user.userid, request.user.upstream_credentials['ops'])

    # System-wide credentials
    else:
        datasource_settings = registry.datasource_settings
        datasources = datasource_settings.datasources
        datasource = datasource_settings.datasource
        if 'ops' in datasources and 'ops' in datasource and 'api_consumer_key' in datasource.ops and 'api_consumer_secret' in datasource.ops:
            system_credentials = {
                'consumer_key': datasource.ops.api_consumer_key,
                'consumer_secret': datasource.ops.api_consumer_secret,
            }
            request.ops_client = pool.get('system', system_credentials)
        else:
            request.ops_client = pool.get('defunct')


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
