# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os
from starlette.exceptions import HTTPException
from patzilla.access.depatech.client import DepaTechClient
from patzilla.access.generic.credentials import AbstractCredentialsGetter

logger = logging.getLogger(__name__)


def create_pool(datasource_settings):

    # Acquire settings for depa.tech.
    depatech_settings = datasource_settings.datasource.depatech

    # Get URI settings, optionally falling back to environment variables.
    api_uri = depatech_settings.get("api_uri", os.environ.get("DEPATECH_API_URI"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using depa.tech API at {}".format(api_uri))
        return DepaTechClientPool(api_uri=api_uri)


class DepaTechCredentialsGetter(AbstractCredentialsGetter):
    """
    Define how to acquire depa.tech credentials from
    configuration settings or environment variables.
    """

    @staticmethod
    def from_settings(datasource_settings):
        datasource = datasource_settings.datasource
        return {
            'api_username': datasource.depatech.api_username,
            'api_password': datasource.depatech.api_password,
        }

    @staticmethod
    def from_environment():
        if not os.environ["DEPATECH_API_USERNAME"] or not os.environ["DEPATECH_API_PASSWORD"]:
            raise KeyError("DEPATECH_API_USERNAME or DEPATECH_API_PASSWORD is empty")
        return {
            "api_username": os.environ["DEPATECH_API_USERNAME"],
            "api_password": os.environ["DEPATECH_API_PASSWORD"],
        }


class DepaTechClientPool:
    """
    depa.tech client pool, holding one client per credentials context.
    """

    def __init__(self, api_uri):
        logger.info("Creating upstream client pool for depa.tech")
        self.api_uri = api_uri
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPException(401, "Unable to discover credentials for depa.tech. identifier={}".format(identifier))

            logger.info("Creating upstream client for depa.tech. identifier={}".format(identifier))
            self.clients[identifier] = DepaTechClient(
                uri=self.api_uri, username=credentials['api_username'], password=credentials['api_password'])

        return self.clients.get(identifier)
