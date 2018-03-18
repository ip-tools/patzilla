.. include:: ../resources.rst

.. _ifi-claims-setup:

####################
Setup CLAIMS® Direct
####################

.. contents::
   :local:
   :depth: 1

----

*****
About
*****
PatZilla uses the CLAIMS® Direct data source by `IFI CLAIMS Patent Services`_
to provide professional access to patent information and worldwide fulltext search.

For general information about the CLAIMS® Direct database, please refer to :ref:`datasource-ifi-claims`.


.. _ifi-claims-account-register:

********************
Account registration
********************

In order to use the CLAIMS® Direct database, you have to get in contact with IFI.
They offer a 30-day free trial for you to preview the database that comes with an onboarding and written trial guide.

Please follow up at: https://www.ificlaims.com/get-started.htm


.. _ifi-claims-system-wide:

*************************
System-wide configuration
*************************
For configuring PatZilla with system-wide CLAIMS® Direct authentication credentials,
please configure the "api_uri", "api_username" and "api_password" settings
in the PatZilla configuration file.

You will find the right place at section ``[datasource:ificlaims]``::

    [datasource:ificlaims]

    # API connection settings
    api_uri      = {ificlaims_api_uri}
    api_username = {ificlaims_api_username}
    api_password = {ificlaims_api_password}


.. _ifi-claims-per-user:

**********************
Per-user configuration
**********************
PatZilla can use per-user credentials for authenticating against the CLAIMS® Direct API.
An example schema for the :ref:`user-model` looks like this::

    upstream_credentials: {
        ificlaims: {
            username: "john.doe",
            password: "Tichbeed"
        }
    }

