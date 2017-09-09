Hash a password
---------------
::

    curl -i localhost:6543/api/identity/pwhash/abc

Authenticate a user
-------------------
::

    curl -i -XPOST -H 'Content-Type: application/json' -d '{"username":"huhu","password":"haha"}' localhost:6543/api/identity/auth
