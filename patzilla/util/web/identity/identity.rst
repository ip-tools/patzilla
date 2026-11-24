Hash a password
---------------
::

    curl -i localhost:6543/api/identity/pwhash/abc

Authenticate a user (password)
------------------------------
::

    curl -i -XPOST -H 'Content-Type: application/json' -d '{"username":"huhu","password":"haha"}' localhost:6543/api/identity/auth

Request an email magic link
---------------------------
::

    curl -i -XPOST -H 'Content-Type: application/json' -d '{"email":"user@example.org","came_from":"/"}' localhost:6543/api/identity/magic-link

Verify a magic link (browser two-step flow)
-------------------------------------------
1. ``GET /auth/magic/verify?token=<token>`` — validates token read-only and renders confirmation page (protects against email link scanners).
2. ``POST /auth/magic/verify`` with form field ``token=<token>`` — atomically consumes the token, provisions/updates the user in MongoDB, creates a server-side session, sets the ``HttpOnly`` session cookie, and redirects.

Inspect current session
-----------------------
::

    curl -i -b cookies.txt localhost:6543/api/identity/session

Sign out (revoke session)
-------------------------
::

    curl -i -XPOST -b cookies.txt -c cookies.txt localhost:6543/api/identity/logout
