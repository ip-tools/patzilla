# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

from starlette.exceptions import HTTPException

from patzilla.access.generic.credentials import AbstractCredentialsGetter
from patzilla.access.sip.client import SipClient

logger = logging.getLogger(__name__)


def create_pool(datasource_settings):

    # Acquire settings for SIP.
    sip_settings = datasource_settings.datasource.sip

    # Get URI settings, optionally falling back to environment variables.
    api_uri = sip_settings.get("api_uri", os.environ.get("SIP_API_URI"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using SIP API at {}".format(api_uri))
        return SipClientPool(api_uri=api_uri)


class SipCredentialsGetter(AbstractCredentialsGetter):
    """
    Define how to acquire SIP credentials from
    configuration settings or environment variables.
    """

    @staticmethod
    def from_settings(datasource_settings):
        datasource = datasource_settings.datasource
        return {
            'api_username': datasource.sip.api_username,
            'api_password': datasource.sip.api_password,
        }

    @staticmethod
    def from_environment():
        if not os.environ["SIP_API_USERNAME"] or not os.environ["SIP_API_PASSWORD"]:
            raise KeyError("SIP_API_USERNAME or SIP_API_PASSWORD is empty")
        return {
            "api_username": os.environ["SIP_API_USERNAME"],
            "api_password": os.environ["SIP_API_PASSWORD"],
        }


class SipClientPool:
    """
    SIP client pool, holding one client per credentials context.
    """

    def __init__(self, api_uri):
        logger.info("Creating upstream client pool for SIP")
        self.api_uri = api_uri
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPException(401, "Unable to discover credentials for SIP. identifier={}".format(identifier))

            logger.info("Creating upstream client for SIP. identifier={}".format(identifier))
            self.clients[identifier] = SipClient(
                uri=self.api_uri, username=credentials['api_username'], password=credentials['api_password'])

        return self.clients.get(identifier)

