# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
from cornice.service import Service
from patzilla.util.web.identity.store import User, UserHistory

log = logging.getLogger(__name__)

def includeme(config):
    config.add_subscriber(attach_user, "pyramid.events.ContextFound")

# ------------------------------------------
#   user injection
# ------------------------------------------
def attach_user(event):
    request = event.request
    registry = request.registry
    #context = request.context
    userid = request.headers.get('X-User-Id')
    if userid:
        request.user = User.objects(userid=userid).first()
    else:
        request.user = User()



# ------------------------------------------
#   services
# ------------------------------------------
identity_auth = Service(
    name='identity-auth',
    path='/api/identity/auth',
    description='Identity service: perform authentication')

identity_pwhash = Service(
    name='identity-pwhash',
    path='/api/identity/pwhash/{password}',
    description='Identity service: hash password')

# TODO: set user password
"""
identity_user_password = Service(
    name='identity-user-password',
    path='/api/identity/user/{username}/{password}',
    description='Identity service: set user password')
"""

# ------------------------------------------
#   handlers
# ------------------------------------------
@identity_auth.post(accept="application/json")
def identity_auth_handler(request):
    """Authenticate a user"""

    payload = request.json
    username = payload.get('username').lower()
    password = payload.get('password')

    # mitigate timing attacks
    # see also:
    # http://codahale.com/a-lesson-in-timing-attacks/
    # http://emerose.com/timing-attacks-explained
    # http://carlos.bueno.org/2011/10/timing.html
    # https://code.djangoproject.com/ticket/20760
    User.crypt500(password)

    # find user
    user = User.objects(username__iexact=username).first()
    if user:

        # check password
        if user.check_password(password):
            UserHistory(userid=user.userid, action='login').save()
            response = {
                'userid': user.userid,
                'username': user.username,
                'fullname': user.fullname,
                'tags': user.tags,
                'modules': user.modules,
            }
            return response

    request.errors.add('identity subsystem', 'authentication-failed', 'Authentication failed')


@identity_pwhash.get(accept="application/json")
def identity_pwhash_handler(request):
    """Hash a password"""

    password = request.matchdict.get('password')
    return User.crypt500(password)
