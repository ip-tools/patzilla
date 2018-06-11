# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from ConfigParser import NoOptionError

from pyramid.httpexceptions import HTTPBadGateway
from zope.interface.declarations import implements
from zope.interface.interface import Interface

from patzilla.access.sip.client import SipClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    datasource_settings = config.registry.datasource_settings
    try:
        api_uri = datasource_settings.datasource.sip.api_uri
    except:
        raise NoOptionError('api_uri', 'datasource:sip')

    config.registry.registerUtility(SipClientPool(api_uri=api_uri))
    config.add_subscriber(attach_sip_client, "pyramid.events.ContextFound")

def attach_sip_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(ISipClientPool)

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('sip'):
        request.sip_client = pool.get(request.user.userid, request.user.upstream_credentials['sip'])

    # System-wide credentials
    else:
        datasource_settings = registry.datasource_settings
        datasources = datasource_settings.datasources
        datasource = datasource_settings.datasource
        if 'sip' in datasources and 'sip' in datasource and 'api_username' in datasource.sip and 'api_password' in datasource.sip:
            system_credentials = {
                'username': datasource.sip.api_username,
                'password': datasource.sip.api_password,
            }
            request.sip_client = pool.get('system', system_credentials)
        else:
            request.sip_client = pool.get('defunct')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class ISipClientPool(Interface):
    pass

class SipClientPool(object):

    implements(ISipClientPool)

    def __init__(self, api_uri):
        self.api_uri = api_uri
        self.clients = {}
        logger.info('Creating SipClientPool')

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('SipClientPool.get: identifier={0}'.format(identifier))
            factory = SipClientFactory(self.api_uri, credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class SipClientFactory(object):

    def __init__(self, api_uri, credentials=None, debug=False):

        self.api_uri = api_uri

        if credentials:
            self.username = credentials['username']
            self.password = credentials['password']

        else:
            message = u'No credentials configured for SIP API.'
            logger.error(u'SipClientFactory: ' + message)
            raise HTTPBadGateway(message)

    def client_create(self):
        client = SipClient(uri=self.api_uri, username=self.username, password=self.password)
        return client
