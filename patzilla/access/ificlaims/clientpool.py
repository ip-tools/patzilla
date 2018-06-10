# -*- coding: utf-8 -*-
# (c) 2015,2016,2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from ConfigParser import NoOptionError
from pyramid.httpexceptions import HTTPBadGateway
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from patzilla.access.ificlaims.client import IFIClaimsClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    datasource_settings = config.registry.datasource_settings
    try:
        api_uri = datasource_settings.datasource.ificlaims.api_uri
    except:
        raise NoOptionError('api_uri', 'datasource:ificlaims')

    config.registry.registerUtility(IFIClaimsClientPool(api_uri=api_uri))
    config.add_subscriber(attach_ificlaims_client, "pyramid.events.ContextFound")

def attach_ificlaims_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(IIFIClaimsClientPool)

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ificlaims'):
        request.ificlaims_client = pool.get(request.user.userid, request.user.upstream_credentials['ificlaims'])

    # System-wide credentials
    else:
        datasource_settings = registry.datasource_settings
        datasources = datasource_settings.datasources
        datasource = datasource_settings.datasource
        if 'ificlaims' in datasources and 'ificlaims' in datasource and 'api_username' in datasource.ificlaims and 'api_password' in datasource.ificlaims:
            system_credentials = {
                'username': datasource.ificlaims.api_username,
                'password': datasource.ificlaims.api_password,
                }
            request.ificlaims_client = pool.get('system', system_credentials)
        else:
            request.ificlaims_client = pool.get('defunct')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IIFIClaimsClientPool(Interface):
    pass

class IFIClaimsClientPool(object):

    implements(IIFIClaimsClientPool)

    def __init__(self, api_uri):
        self.api_uri = api_uri
        self.clients = {}
        logger.info('Creating IFIClaimsClientPool')

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('IFIClaimsClientPool.get: identifier={0}'.format(identifier))
            factory = IFIClaimsClientFactory(self.api_uri, credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class IFIClaimsClientFactory(object):

    def __init__(self, api_uri, credentials=None, debug=False):

        self.api_uri = api_uri

        if credentials:
            self.username = credentials['username']
            self.password = credentials['password']

        else:
            message = u'No credentials configured for IFI CLAIMS API.'
            logger.error(u'IFIClaimsClientFactory: ' + message)
            raise HTTPBadGateway(message)

        #if debug:
        #    logging.getLogger('oauthlib').setLevel(logging.DEBUG)

    def client_create(self):
        client = IFIClaimsClient(uri=self.api_uri, username=self.username, password=self.password)
        return client
