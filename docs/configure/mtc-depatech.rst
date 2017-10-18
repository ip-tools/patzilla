.. include:: ../resources.rst

.. _mtc-depatech-setup:

###################
depa.tech api setup
###################

.. contents::
   :local:
   :depth: 1

----

*****
About
*****
PatZilla uses the `depa.tech api`_ data source to provide professional access to
patent information and fulltext search across DE, EP, WO, US, JP and KR.

For general information about the depa.tech api, please refer to :ref:`datasource-mtc-depatech`.


.. _mtc-depatech-account-register:

********************
Account registration
********************
To get access to their public APIs, the customer must have an account for their depatech-proxy (basic authentication).
They will provide you such an account by sending an email to marc.haus@mtc.berlin
or by visiting the `depa.tech api`_ page.


.. _mtc-depatech-system-wide:

*************************
System-wide configuration
*************************
For configuring PatZilla with system-wide `depa.tech api`_ authentication credentials,
please configure the "api_uri", "api_username" and "api_password" settings
in the PatZilla configuration file.

You will find the right place at section ``[datasource_depatech]``::

    [datasource_depatech]

    # API connection settings
    api_uri      = {depatech_api_uri}
    api_username = {depatech_api_username}
    api_password = {depatech_api_password}


.. _mtc-depatech-per-user:

**********************
Per-user configuration
**********************
PatZilla can use per-user credentials for authenticating against the `depa.tech api`_.
An example schema for the :ref:`user-model` looks like this::

    upstream_credentials: {
        depatech: {
            username: "john.doe",
            password: "ogdotdut"
        }
    }

