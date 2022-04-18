# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging

import attr

logger = logging.getLogger(__name__)


class AbstractCredentialsGetter(object):

    @staticmethod
    def from_settings(datasource_settings):
        pass

    @staticmethod
    def from_environment():
        pass


@attr.s
class DatasourceCredentialsManager(object):
    """
    Progressively discover data source credentials by probing different locations.
    The contexts probed, in this very order, are: user, vendor, system, machine.

    In this manner, user-associated credentials always take precedence over any
    others. The others will only be used as fallbacks when the user has no
    credentials associated with her account.
    """

    identifier = attr.ib(type=str)
    credentials_getter = attr.ib(type=AbstractCredentialsGetter)

    def resolve(self, request):

        logger.debug("Getting credentials for data source: {}".format(self.identifier))

        registry = request.registry

        vendor_settings = request.runtime_settings.vendor

        credentials_source = None
        credentials_data = None

        # Check user-associated credentials.
        if request.user and request.user.upstream_credentials and request.user.upstream_credentials.has_key(self.identifier):
            credentials_source = request.user.userid
            credentials_data = request.user.upstream_credentials[self.identifier]

        # Check vendor-wide credentials.
        elif vendor_settings and 'datasource_settings' in vendor_settings:
            try:
                credentials_source = 'vendor'
                credentials_data = self.credentials_getter.from_settings(vendor_settings.datasource_settings)
            except:
                pass

        # Fall back to system-wide credentials.
        if not credentials_data:
            try:
                credentials_source = 'system'
                credentials_data = self.credentials_getter.from_settings(registry.datasource_settings)
            except:
                pass

        # Fall back to machine-wide credentials from environment variables.
        if not credentials_data:
            try:
                credentials_source = 'machine'
                credentials_data = self.credentials_getter.from_environment()
            except Exception as ex:
                logger.warning("Discovering credentials from environment variables failed. "
                               "Reason: {}: {}".format(ex.__class__.__name__, ex))

        # When there are still no credentials found, croak hard.
        if not credentials_data:
            msg = "No credentials configured for data source: {}".format(self.identifier)
            logger.critical(msg)
            raise RuntimeError(msg)

        return credentials_source, credentials_data
