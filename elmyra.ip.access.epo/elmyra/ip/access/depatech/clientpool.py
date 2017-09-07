# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import logging
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from elmyra.ip.access.depatech.client import DepaTechClient

logger = logging.getLogger(__name__)

# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_oauth_client_pool, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(DepaTechClientPool())
    config.add_subscriber(attach_depatech_client, "pyramid.events.ContextFound")

def attach_depatech_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(IDepaTechClientPool)
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('depatech'):
        request.depatech_client = pool.get(request.user.userid, request.user.upstream_credentials['depatech'])
    else:
        request.depatech_client = pool.get('default')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IDepaTechClientPool(Interface):
    pass

class DepaTechClientPool(object):

    implements(IDepaTechClientPool)

    def __init__(self):
        self.clients = {}
        print 'DepaTechClientPool.__init__'

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('DepaTechClientPool.get: identifier={0}'.format(identifier))
            factory = DepaTechClientFactory(credentials=credentials, debug=False)
            self.clients[identifier] = factory.client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class DepaTechClientFactory(object):

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
        client = DepaTechClient(uri='***REMOVED***', username=self.username, password=self.password)
        return client
