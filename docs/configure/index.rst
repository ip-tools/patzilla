.. _configuration:

#############
Configuration
#############
This part of the documentation covers the configuration of PatZilla.
The second step to using any software package is getting it properly configured.
Please read this section carefully.

After successfully installing the software, you might want to
follow up about :ref:`running` it.


******************************
Application configuration file
******************************
Blueprints of configuration files for running PatZilla
in development and production mode are shipped with the
Python package.

In order to copy the *production* PatZilla configuration
blueprint to the designated location, issue::

    patzilla make-config production > /path/to/patzilla.ini


********
Database
********
Please edit the ``patzilla.ini`` created above and have a look at the ``[app:main]`` section.
The database configuration settings for connecting to a MongoDB daemon are::

    # Database configuration
    mongodb.patzilla.uri = mongodb://localhost:27017/patzilla

    # Cache settings
    cache.url = mongodb://localhost:27017/beaker.cache


************
Data sources
************
Configure the data source web services PatZilla should use for accessing patent information.
Some primary data sources are obligatory, some are optional.

Please refer to the documentation section :ref:`data-sources` for an overview
about the data sources PatZilla can handle.

For datasource configuration, please edit the ``patzilla.ini`` created above and
edit these sections according to your needs:

- ``[ip_navigator]``::

    # Which datasources are configured?
    datasources = ops, ificlaims, depatech

- :ref:`OPS API <epo-ops-system-wide>` (Please go to :ref:`epo-ops-account-register` first)::

    [datasource_ops]

    # Application-wide authentication credentials
    api_consumer_key    = {ops_api_consumer_key}
    api_consumer_secret = {ops_api_consumer_secret}

- :ref:`CLAIMS® Direct API <ifi-claims-system-wide>`::

    [datasource_ificlaims]

    # API connection settings
    api_uri      = {ificlaims_api_uri}
    api_username = {ificlaims_api_username}
    api_password = {ificlaims_api_password}

- :ref:`depa.tech API <mtc-depatech-system-wide>`::

    [datasource_depatech]

    # API connection settings
    api_uri      = {depatech_api_uri}
    api_username = {depatech_api_username}
    api_password = {depatech_api_password}


*************
User database
*************
To provision user accounts, please refer to the :ref:`user-model`.
