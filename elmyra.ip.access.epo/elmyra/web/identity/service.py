# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
import logging
from cornice.service import Service
from elmyra.web.identity.store import User

log = logging.getLogger(__name__)


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
    username = payload.get('username')
    password = payload.get('password')

    # mitigate timing attacks
    # see also:
    # http://codahale.com/a-lesson-in-timing-attacks/
    # http://emerose.com/timing-attacks-explained
    # http://carlos.bueno.org/2011/10/timing.html
    # https://code.djangoproject.com/ticket/20760
    User.crypt500(password)

    # find user
    user = User.objects(username=username).first()
    if user:

        # check password
        if user.check_password(password):
            response = {
                'userid': user.userid,
                'username': user.username,
                'fullname': user.fullname,
            }
            return response

    request.errors.add('identity subsystem', 'authentication-failed', 'Authentication failed')


@identity_pwhash.get(accept="application/json")
def identity_pwhash_handler(request):
    """Hash a password"""

    password = request.matchdict.get('password')
    return User.crypt500(password)
