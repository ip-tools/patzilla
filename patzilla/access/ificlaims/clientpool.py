# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

from starlette.exceptions import HTTPException

from patzilla.access.generic.credentials import AbstractCredentialsGetter
from patzilla.access.ificlaims.client import IFIClaimsClient

logger = logging.getLogger(__name__)


def create_pool(datasource_settings):

    # Acquire settings for IFI CLAIMS.
    ificlaims_settings = datasource_settings.datasource.ificlaims

    # Get URI settings, optionally falling back to environment variables.
    api_uri = ificlaims_settings.get("api_uri", os.environ.get("IFICLAIMS_API_URI"))
    api_uri_json = ificlaims_settings.get("api_uri_json", os.environ.get("IFICLAIMS_API_URI_JSON"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using IFI CLAIMS API at {}".format(api_uri))
        return IFIClaimsClientPool(api_uri=api_uri, api_uri_json=api_uri_json)


class IfiClaimsCredentialsGetter(AbstractCredentialsGetter):
    """
    Define how to acquire IFI CLAIMS credentials from
    configuration settings or environment variables.
    """

    @staticmethod
    def from_settings(datasource_settings):
        datasource = datasource_settings.datasource
        return {
            'api_username': datasource.ificlaims.api_username,
            'api_password': datasource.ificlaims.api_password,
        }

    @staticmethod
    def from_environment():
        if not os.environ["IFICLAIMS_API_USERNAME"] or not os.environ["IFICLAIMS_API_PASSWORD"]:
            raise KeyError("IFICLAIMS_API_USERNAME or IFICLAIMS_API_PASSWORD is empty")
        return {
            "api_username": os.environ["IFICLAIMS_API_USERNAME"],
            "api_password": os.environ["IFICLAIMS_API_PASSWORD"],
        }


class IFIClaimsClientPool:
    """
    IFI CLAIMS client pool, holding one client per credentials context.
    """


    def __init__(self, api_uri, api_uri_json):
        logger.info("Creating upstream client pool for IFI CLAIMS")
        self.api_uri = api_uri
        self.api_uri_json = api_uri_json
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPException(401, "Unable to discover credentials for IFI CLAIMS. identifier={}".format(identifier))

            if debug:
                logging.getLogger('oauthlib').setLevel(logging.DEBUG)

            logger.info("Creating upstream client for IFI CLAIMS. identifier={}".format(identifier))
            self.clients[identifier] = IFIClaimsClient(
                self.api_uri, self.api_uri_json, credentials['api_username'], credentials['api_password'])

        return self.clients.get(identifier)
