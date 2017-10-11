# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl, Elmyra UG
import time
import json
import logging
import requests
from pyramid.httpexceptions import HTTPBadGateway
from pyramid.threadlocal import get_current_registry
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from requests_oauthlib.oauth2_session import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient, OAuth2Error
from oauthlib.common import add_params_to_uri
from patzilla.access.epo.ops.api import OPS_AUTH_URI, OPS_API_URI
from patzilla.util.web.identity.store import IUserMetricsManager

logger = logging.getLogger(__name__)


# ------------------------------------------
#   bootstrapping
# ------------------------------------------
def includeme(config):
    #config.add_subscriber(setup_oauth_client_pool, "pyramid.events.ApplicationCreated")
    config.registry.registerUtility(OpsClientPool())
    config.add_subscriber(attach_oauth_client, "pyramid.events.ContextFound")

def attach_oauth_client(event):
    #logger.info('Attaching OAuth client to request')

    request = event.request
    registry = request.registry

    pool = registry.getUtility(IOpsClientPool)

    # User-associated credentials
    if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key('ops'):
        request.ops_oauth_client = pool.get(request.user.userid, request.user.upstream_credentials['ops'])

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
            request.ops_oauth_client = pool.get('system', system_credentials)
        else:
            request.ops_oauth_client = pool.get('defunct')


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
            # TODO: Use "debug" flag from some configuration setting
            factory = OpsOAuthClientFactory(credentials=credentials, debug=False)
            self.clients[identifier] = factory.create_session(identifier=identifier)
        return self.clients.get(identifier)


# ------------------------------------------
#   implementation
# ------------------------------------------
class OpsOAuth2Session(OAuth2Session):

    def __init__(self, *args, **kwargs):

        registry = get_current_registry()

        # Remember the last throttling message in order to emit only changes to the log
        self.throttle_last_log = None

        # Create metrics manager per OAuth session
        self.metrics_manager = registry.getUtility(IUserMetricsManager)

        # Pass execution flow to parent constructor
        super(OpsOAuth2Session, self).__init__(*args, **kwargs)

    def request(self, *args, **kwargs):

        #pprint(args)
        #pprint(kwargs)

        try:
            kwargs_real = kwargs.copy()
            if 'provoke_failure' in kwargs:
                del kwargs['provoke_failure']

            response = super(OpsOAuth2Session, self).request(*args, **kwargs)

            # Debug path
            if 'provoke_failure' in kwargs_real:
                response.status_code = 403
                response.headers['X-Anonymousquotaperminute-Used'] = '5'

            # When OAuth authorization is lost, invalidate token and close connection
            if self.is_anonymous(response):
                self.disconnect()

            # Success path
            content_length = response.headers.get('Content-Length')
            if content_length and content_length.isdigit():
                self.metrics_manager.measure_upstream('ops', int(content_length))

            # Log X-Throttling-Control response header
            x_throttling_control = response.headers.get('x-throttling-control')
            if x_throttling_control:

                # Counter duplicate header problem, sometimes we receive duplicate lines like:
                # idle (images=green:200, inpadoc=green:60, other=green:1000, retrieval=green:200, search=green:30), idle (images=green:200, inpadoc=green:60, other=green:1000, retrieval=green:200, search=green:30)
                if len(x_throttling_control) > 150:
                    x_throttling_control = x_throttling_control[:len(x_throttling_control)/2].strip(' ,')
                if x_throttling_control != self.throttle_last_log:
                    self.throttle_last_log = x_throttling_control
                    logger.info('OPS X-Throttling-Control: {0}'.format(x_throttling_control))

                # Kick in throttling on our side
                # TODO: Improve context sensitivity, i.e. look at individual performance status attributes
                """
                Busy situation::

                    idle (images=green:200, inpadoc=green:60, other=green:1000, retrieval=green:200, search=green:30)
                    busy (images=green:100, inpadoc=green:45, other=green:1000, retrieval=green:100, search=green:15)
                    idle (images=green:200, inpadoc=green:60, other=green:1000, retrieval=green:200, search=green:30)
                    busy (images=green:100, inpadoc=green:45, other=green:1000, retrieval=green:100, search=green:15)

                Overload situation::

                    busy       (images=black:0, inpadoc=green:45, other=green:1000, retrieval=green:100, search=green:15)
                    overloaded (images=black:0, inpadoc=green:30, other=green:1000, retrieval=green:50, search=green:5)

                """
                busyness_kind = None
                throttle_wait = None
                if x_throttling_control.startswith('busy'):
                    busyness_kind = 'busy'
                    throttle_wait = 0.33
                elif x_throttling_control.startswith('overloaded'):
                    busyness_kind = 'overloaded'
                    throttle_wait = 0.75

                if throttle_wait:
                    logger.info('OPS is {busyness_kind}, delaying request for {seconds} seconds'.format(
                        busyness_kind=busyness_kind, seconds=throttle_wait))
                    time.sleep(throttle_wait)

            return response

        except OAuth2Error as ex:
            ex.url = ex.uri
            ex.content = ex.description
            logger.error('OpsOAuth2Session {0}: {1}. client_id={2}'.format(ex.__class__.__name__, ex.description, self.client_id))
            self.disconnect()
            return ex

        except requests.exceptions.ConnectionError as ex:
            logger.error('OpsOAuth2Session {0}: {1}. client_id={2}'.format(ex.__class__.__name__, ex, self.client_id))
            self.disconnect()
            # Fake an exception which can be processed by downstream error handling infrastructure
            error = HTTPBadGateway(u'Network error: Could not connect to OPS servers.')
            raise error

        except requests.exceptions.HTTPError as ex:
            logger.error('OpsOAuth2Session {0}: {1}. client_id={2}'.format(ex.__class__.__name__, ex, self.client_id))
            self.disconnect()

            # Fake an exception which can be processed by downstream error handling infrastructure
            if hasattr(ex, 'response'):
                error = HTTPBadGateway(u'Could not connect to OPS servers.')
                error.code = int(ex.response.status_code)
                error.status_code = ex.response.status_code
                error.content_type = ex.response.content_type
                error.explanation = ex.response.content
                raise error

    def disconnect(self, *args, **kwargs):
        logger.warning('Invalidating token and closing connection for client_id={client_id}'.format(client_id=self.client_id))
        self.token = self.get_empty_token()
        return self.close(*args, **kwargs)

    def is_anonymous(self, response):
        """

        # Anonymous access
        'x-anonymousquotaperminute-used': '1'
        'x-anonymousquotaperday-used': '10514'
        'x-individualquotaperhour-used': '31544'

        # Rejected after running into a quota limit
        'x-rejection-reason': 'AnonymousQuotaPerDay'

        # Authenticated access
        'x-individualquotaperhour-used': '26287'
        'x-registeredpayingquotaperweek-used': '375005228'

        """
        if 'x-anonymousquotaperminute-used' in response.headers or \
           'x-anonymousquotaperday-used' in  response.headers:
            return True
        else:
            return False

    @classmethod
    def get_empty_token(cls):
        token = {
            'access_token': 'UNKNOWN',
            'token_type': 'Bearer',
            'expires_in': '-30',     # initially 3600, need to be updated by you
        }
        return token


class OpsOAuthClientFactory(object):

    def __init__(self, credentials=None, debug=False):

        if credentials:
            self.consumer_key    = credentials['consumer_key']
            self.consumer_secret = credentials['consumer_secret']

        else:
            message = u'No credentials configured for OPS API.'
            logger.error(u'OpsOAuthClientFactory: ' + message)
            raise HTTPBadGateway(message)

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
                error_text = response.text
                if 'ClientId is Invalid' in response.text:
                    error_name = 'invalid_client_id'
                    error_text = 'ClientId is Invalid'
                if 'Client credentials are invalid' in response.text:
                    error_name = 'access_denied'
                    error_text = 'Client credentials are invalid'

                oauth_error = {
                    'error': error_name,
                    'error_description': 'OAuth error: {0}'.format(error_text),
                    'error_uri': response.url,
                }

                response.content_type = 'application/json'
                response._content = json.dumps(oauth_error)

                response.raise_for_status()

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

    def create_session(self, identifier=None):

        client_id     = self.consumer_key
        client_secret = self.consumer_secret

        logger.info('OpsOAuthClientFactory.create_session: ' \
                    'identifier={identifier}, client_id={client_id}'.format(**locals()))

        token_url = OPS_AUTH_URI + '/accesstoken'
        refresh_url = token_url

        extra = {
            'client_id':     client_id,
            'client_secret': client_secret,
        }

        def token_saver(token):
            #print "token_saver:", token
            pass

        client = BackendApplicationClient(client_id)
        client.prepare_refresh_body = client.prepare_request_body
        #print "BackendApplicationClient.request_body:", client.prepare_request_body()
        #'grant_type=client_credentials&scope=hello+world'

        empty_token = OpsOAuth2Session.get_empty_token()
        session = OpsOAuth2Session(
            client_id=client_id,
            client=client,
            auto_refresh_url=refresh_url, auto_refresh_kwargs=extra,
            token=empty_token, token_updater=token_saver)

        self.ops_compliance_fix(session)

        return session
