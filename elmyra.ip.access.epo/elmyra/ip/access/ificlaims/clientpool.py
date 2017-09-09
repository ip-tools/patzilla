# -*- coding: utf-8 -*-
# (c) 2015,2016,2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from ConfigParser import NoOptionError
from pyramid.httpexceptions import HTTPBadGateway
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from elmyra.ip.access.ificlaims.client import IFIClaimsClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    application_settings = config.registry.application_settings
    try:
        api_url = application_settings.datasource_ificlaims.api_url
    except:
        raise NoOptionError('api_url', 'datasource_ificlaims')

    config.registry.registerUtility(IFIClaimsClientPool(api_url=api_url))
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
        if 'ificlaims' in datasources and 'ificlaims' in datasource and 'username' in datasource.ificlaims and 'password' in datasource.ificlaims:
            system_credentials = {
                'username': datasource.ificlaims.username,
                'password': datasource.ificlaims.password,
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

    def __init__(self, api_url):
        self.api_url = api_url
        self.clients = {}
        logger.info('Creating IFIClaimsClientPool')

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('IFIClaimsClientPool.get: identifier={0}'.format(identifier))
            factory = IFIClaimsClientFactory(self.api_url, credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class IFIClaimsClientFactory(object):

    def __init__(self, api_url, credentials=None, debug=False):

        self.api_url = api_url

        if credentials:
            self.username = credentials['username']
            self.password = credentials['password']

        else:
            message = u'No credentials configured for IFI Claims API.'
            logger.error(u'IFIClaimsClientFactory: ' + message)
            raise HTTPBadGateway(message)

        #if debug:
        #    logging.getLogger('oauthlib').setLevel(logging.DEBUG)

    def client_create(self):
        client = IFIClaimsClient(uri=self.api_url, username=self.username, password=self.password)
        return client
