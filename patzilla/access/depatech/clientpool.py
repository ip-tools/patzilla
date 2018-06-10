# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from ConfigParser import NoOptionError
from pyramid.httpexceptions import HTTPBadGateway
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from patzilla.access.depatech.client import DepaTechClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    datasource_settings = config.registry.datasource_settings
    try:
        api_uri = datasource_settings.datasource.depatech.api_uri
    except:
        raise NoOptionError('api_uri', 'datasource:depatech')

    config.registry.registerUtility(DepaTechClientPool(api_uri=api_uri))
    config.add_subscriber(attach_depatech_client, "pyramid.events.ContextFound")

def attach_depatech_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(IDepaTechClientPool)

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('depatech'):
        request.depatech_client = pool.get(request.user.userid, request.user.upstream_credentials['depatech'])

    # System-wide credentials
    else:
        datasource_settings = registry.datasource_settings
        datasources = datasource_settings.datasources
        datasource = datasource_settings.datasource
        if 'depatech' in datasources and 'depatech' in datasource and 'api_username' in datasource.depatech and 'api_password' in datasource.depatech:
            system_credentials = {
                'username': datasource.depatech.api_username,
                'password': datasource.depatech.api_password,
                }
            request.depatech_client = pool.get('system', system_credentials)
        else:
            request.depatech_client = pool.get('defunct')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IDepaTechClientPool(Interface):
    pass

class DepaTechClientPool(object):

    implements(IDepaTechClientPool)

    def __init__(self, api_uri):
        self.api_uri = api_uri
        self.clients = {}
        logger.info('Creating DepaTechClientPool')

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('DepaTechClientPool.get: identifier={0}'.format(identifier))
            factory = DepaTechClientFactory(self.api_uri, credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class DepaTechClientFactory(object):

    def __init__(self, api_uri, credentials=None, debug=False):

        self.api_uri = api_uri

        if credentials:
            self.username = credentials['username']
            self.password = credentials['password']

        else:
            message = u'No credentials configured for depa.tech API.'
            logger.error(u'DepaTechClientFactory: ' + message)
            raise HTTPBadGateway(message)


        #if debug:
        #    logging.getLogger('oauthlib').setLevel(logging.DEBUG)

    def client_create(self):
        client = DepaTechClient(uri=self.api_uri, username=self.username, password=self.password)
        return client
