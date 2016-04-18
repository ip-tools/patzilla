# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from elmyra.ip.access.ificlaims.client import IFIClaimsClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_oauth_client_pool, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(IFIClaimsClientPool())
    config.add_subscriber(attach_ificlaims_client, "pyramid.events.ContextFound")

def attach_ificlaims_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(IIFIClaimsClientPool)
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ificlaims'):
        request.ificlaims_client = pool.get(request.user.userid, request.user.upstream_credentials['ificlaims'])
    else:
        request.ificlaims_client = pool.get('default')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IIFIClaimsClientPool(Interface):
    pass

class IFIClaimsClientPool(object):

    implements(IIFIClaimsClientPool)

    def __init__(self):
        self.clients = {}
        print 'IFIClaimsClientPool.__init__'

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('IFIClaimsClientPool.get: identifier={0}'.format(identifier))
            factory = IFIClaimsClientFactory(credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class IFIClaimsClientFactory(object):

    def __init__(self, credentials=None, debug=False):

        if credentials:
            # User-associated credentials
            self.username = credentials['username']
            self.password = credentials['password']
        else:
            # Elmyra credentials
            self.username = r'***REMOVED***'
            self.password = r'***REMOVED***'

            #if debug:
            #    logging.getLogger('oauthlib').setLevel(logging.DEBUG)

    def client_create(self):
        client = IFIClaimsClient(uri='https://cdws.ificlaims.com', username=self.username, password=self.password)
        return client
