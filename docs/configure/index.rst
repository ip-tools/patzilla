.. _configuration:

#############
Configuration
#############
This part of the documentation covers the configuration of PatZilla.
The second step to using any software package is getting it properly configured.
Please read this section carefully.


******************************
Application configuration file
******************************
Blueprints of configuration files for running PatZilla
in development and production mode are shipped with the
Python package.

In order to copy the *production* PatZilla configuration
blueprint to the designated location, issue::

    patzilla make-config production > /path/to/patzilla.ini




********************
Third-party services
********************
PatZilla relies on a number of third-party services for accessing patent information.
Some primary data sources are obligatory, some are optional.

Please refer to the documentation section :ref:`data-sources` for an overview
about the data sources PatZilla can handle.


*************
User database
*************
To provision user accounts, please refer to the :ref:`user-model`.
