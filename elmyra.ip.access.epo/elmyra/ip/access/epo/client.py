import json
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib.oauth2_session import OAuth2Session
from oauthlib.common import add_params_to_uri

def ops_compliance_fix(session):

    def _missing_token_type(r):
        #print "======================================= _missing_token_type"
        token = json.loads(r.text)
        if 'token_type' in token and token['token_type'] == 'BearerToken':
            token['token_type'] = 'Bearer'
        r._content = json.dumps(token)
        return r

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

def oauth_client_create():
    token = {
        'access_token': 'eswfld123kjhn1v5423',
        'refresh_token': 'asdfkljh23490sdf',
        'token_type': 'Bearer',
        'expires_in': '-30',     # initially 3600, need to be updated by you
    }

    consumer_key = r'***REMOVED***'
    consumer_secret = r'***REMOVED***'
    token_url = 'https://ops.epo.org/3.1/auth/accesstoken'
    refresh_url = token_url

    extra = {
        'client_id': consumer_key,
        'client_secret': consumer_secret,
    }

    def token_saver(token):
        #print "token_saver:", token
        pass

    client = BackendApplicationClient(consumer_key)
    client.prepare_refresh_body = client.prepare_request_body
    #print "BackendApplicationClient.request_body:", client.prepare_request_body()
    #'grant_type=client_credentials&scope=hello+world'

    #print "OAuth2Session start"
    session = OAuth2Session(
        client_id=consumer_key,
        client=client,
        auto_refresh_url=refresh_url, auto_refresh_kwargs=extra,
        token=token, token_updater=token_saver)

    ops_compliance_fix(session)

    return session
