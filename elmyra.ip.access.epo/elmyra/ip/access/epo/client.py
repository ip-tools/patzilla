# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import json
import logging
from oauthlib.oauth2 import BackendApplicationClient, OAuth2Error
from pyramid.threadlocal import get_current_registry
from requests.exceptions import ConnectionError
from requests_oauthlib.oauth2_session import OAuth2Session
from oauthlib.common import add_params_to_uri
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from elmyra.web.identity.store import IUserMetricsManager

logger = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_oauth_client_pool, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(OpsOAuthClientPool())
    config.add_subscriber(attach_oauth_client, "pyramid.events.ContextFound")

def attach_oauth_client(event):
    request = event.request
    registry = request.registry
    #context = request.context

    pool = registry.getUtility(IOpsOAuthClientPool)
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ops'):
        request.ops_oauth_client = pool.get(request.user.userid, request.user.upstream_credentials['ops'])
    else:
        request.ops_oauth_client = pool.get('default')


# ------------------------------------------
#   pool as utility
# ------------------------------------------
class IOpsOAuthClientPool(Interface):
    pass

class OpsOAuthClientPool(object):

    implements(IOpsOAuthClientPool)

    def __init__(self):
        self.clients = {}
        print 'OpsOAuthClientPool.__init__'

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            logger.info('OpsOAuthClientPool.get: identifier={0}'.format(identifier))
            factory = OpsOAuthClientFactory(credentials=credentials, debug=False)
            self.clients[identifier] = factory.oauth_client_create()
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class OpsOAuth2Session(OAuth2Session):

    def __init__(self, *args, **kwargs):
        registry = get_current_registry()
        self.metrics_manager = registry.getUtility(IUserMetricsManager)
        super(OpsOAuth2Session, self).__init__(*args, **kwargs)

    def request(self, *args, **kwargs):

        try:
            response = super(OpsOAuth2Session, self).request(*args, **kwargs)
            content_length = response.headers.get('Content-Length')
            if content_length and content_length.isdigit():
                self.metrics_manager.measure_upstream('ops', int(content_length))

            # FIXME: Temporary logging
            logger.info('OPS X-Throttling-Control: {0}'.format(response.headers.get('x-throttling-control')))

            return response

        except (ConnectionError, OAuth2Error) as ex:
            ex.url = ex.uri
            ex.content = ex.description
            logger.error('OpsOAuth2Session {0} {1}. client_id={2}'.format(ex.__class__.__name__, ex.description, self.client_id))
            return ex


class OpsOAuthClientFactory(object):

    def __init__(self, credentials=None, debug=False):

        if credentials:
            # User-associated OPS credentials
            self.consumer_key    = credentials['consumer_key']
            self.consumer_secret = credentials['consumer_secret']
        else:
            # Elmyra OPS credentials
            self.consumer_key    = r'***REMOVED***'
            self.consumer_secret = r'***REMOVED***'

        if debug:
            logging.getLogger('oauthlib').setLevel(logging.DEBUG)

    def ops_compliance_fix(self, session):

        def _missing_token_type(response):

            if response.status_code == 200:
                token = json.loads(response.text)
                if 'token_type' in token and token['token_type'] == 'BearerToken':
                    token['token_type'] = 'Bearer'
                response._content = json.dumps(token)

            else:

                error_name = None
                if 'ClientId is Invalid' in response.text:
                    error_name = 'invalid_client_id'
                if 'Client credentials are invalid' in response.text:
                    error_name = 'access_denied'

                oauth_error = {
                    'error': error_name,
                    'error_description': 'OAuth error: {0}'.format(response.text),
                    'error_uri': response.url,
                }

                response.content_type = 'application/json'
                response._content = json.dumps(oauth_error)

            return response

        def _non_compliant_param_name(url, headers, data):
            token = [('oauth2_access_token', session._client.access_token)]
            url = add_params_to_uri(url, token)
            return url, headers, data

        #session._client.default_token_placement = 'query'
        #print "================================ register_compliance_hook"
        session.register_compliance_hook('access_token_response', _missing_token_type)
        session.register_compliance_hook('refresh_token_response', _missing_token_type)
        #session.register_compliance_hook('protected_request', _non_compliant_param_name)
        return session

    def oauth_client_create(self):

        #print '========= oauth_client_create'

        token = {
            'access_token': 'eswfld123kjhn1v5423',
            'refresh_token': 'asdfkljh23490sdf',
            'token_type': 'Bearer',
            'expires_in': '-30',     # initially 3600, need to be updated by you
        }

        token_url = 'https://ops.epo.org/3.1/auth/accesstoken'
        refresh_url = token_url

        extra = {
            'client_id': self.consumer_key,
            'client_secret': self.consumer_secret,
        }

        def token_saver(token):
            #print "token_saver:", token
            pass

        client = BackendApplicationClient(self.consumer_key)
        client.prepare_refresh_body = client.prepare_request_body
        #print "BackendApplicationClient.request_body:", client.prepare_request_body()
        #'grant_type=client_credentials&scope=hello+world'

        #print "OAuth2Session start"
        session = OpsOAuth2Session(
            client_id=self.consumer_key,
            client=client,
            auto_refresh_url=refresh_url, auto_refresh_kwargs=extra,
            token=token, token_updater=token_saver)

        self.ops_compliance_fix(session)

        return session
