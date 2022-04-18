# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os
from pyramid.httpexceptions import HTTPUnauthorized
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from patzilla.access.depatech.client import DepaTechClient
from patzilla.access.generic.credentials import AbstractCredentialsGetter, DatasourceCredentialsManager

logger = logging.getLogger(__name__)


def includeme(config):

    # Acquire settings for depa.tech.
    datasource_settings = config.registry.datasource_settings
    depatech_settings = datasource_settings.datasource.depatech

    # Get URI settings, optionally falling back to environment variables.
    api_uri = depatech_settings.get("api_uri", os.environ.get("DEPATECH_API_URI"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using depa.tech API at {}".format(api_uri))
        config.registry.registerUtility(DepaTechClientPool(api_uri=api_uri))
        config.add_subscriber(attach_depatech_client, "pyramid.events.ContextFound")


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
        return {
            "api_username": os.environ["DEPATECH_API_USERNAME"],
            "api_password": os.environ["DEPATECH_API_PASSWORD"],
        }


def attach_depatech_client(event):
    """
    Create depa.tech client pool per credentials context.
    """

    # Don't start data source machinery on requests to static assets.
    if '/static' in event.request.url:
        return

    request = event.request

    try:
        dcm = DatasourceCredentialsManager(identifier="depatech", credentials_getter=DepaTechCredentialsGetter)
        credentials_source, credentials_data = dcm.resolve(request)
    except:
        logger.exception("Unable to resolve credentials for depa.tech")
        return

    username = credentials_data['api_username'][:10]
    logger.debug('Attaching depa.tech credentials from "{}": {}'.format(credentials_source, username))

    pool = request.registry.getUtility(IDepaTechClientPool)
    request.depatech_client = pool.get(credentials_source, credentials_data)


class IDepaTechClientPool(Interface):
    pass


class DepaTechClientPool(object):
    """
    depa.tech client pool as Pyramid utility implementation.
    """

    implements(IDepaTechClientPool)

    def __init__(self, api_uri):
        logger.info("Creating upstream client pool for depa.tech")
        self.api_uri = api_uri
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPUnauthorized("Unable to discover credentials for depa.tech. identifier={}".format(identifier))

            logger.info("Creating upstream client for depa.tech. identifier={}".format(identifier))
            self.clients[identifier] = DepaTechClient(
                uri=self.api_uri, username=credentials['api_username'], password=credentials['api_password'])

        return self.clients.get(identifier)
