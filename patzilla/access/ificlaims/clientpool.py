# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

from pyramid.httpexceptions import HTTPUnauthorized
from zope.interface.declarations import implements
from zope.interface.interface import Interface

from patzilla.access.generic.credentials import AbstractCredentialsGetter, DatasourceCredentialsManager
from patzilla.access.ificlaims.client import IFIClaimsClient

logger = logging.getLogger(__name__)


def includeme(config):

    # Acquire settings for IFI CLAIMS.
    datasource_settings = config.registry.datasource_settings
    ificlaims_settings = datasource_settings.datasource.ificlaims

    # Get URI settings, optionally falling back to environment variables.
    api_uri = ificlaims_settings.get("api_uri", os.environ.get("IFICLAIMS_API_URI"))
    api_uri_json = ificlaims_settings.get("api_uri_json", os.environ.get("IFICLAIMS_API_URI_JSON"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using IFI CLAIMS API at {}".format(api_uri))
        config.registry.registerUtility(IFIClaimsClientPool(api_uri=api_uri, api_uri_json=api_uri_json))
        config.add_subscriber(attach_ificlaims_client, "pyramid.events.ContextFound")


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
        return {
            "api_username": os.environ["IFICLAIMS_API_USERNAME"],
            "api_password": os.environ["IFICLAIMS_API_PASSWORD"],
        }


def attach_ificlaims_client(event):
    """
    Create IFI CLAIMS client pool per credentials context.
    """

    # Don't start data source machinery on requests to static assets.
    if '/static' in event.request.url:
        return

    request = event.request

    try:
        dcm = DatasourceCredentialsManager(identifier="ificlaims", credentials_getter=IfiClaimsCredentialsGetter)
        credentials_source, credentials_data = dcm.resolve(request)
    except:
        logger.exception("Unable to resolve credentials for IFI CLAIMS")
        return

    username = credentials_data['api_username'][:10]
    logger.debug('Attaching IFI CLAIMS credentials from "{}": {}'.format(credentials_source, username))

    pool = request.registry.getUtility(IIFIClaimsClientPool)
    request.ificlaims_client = pool.get(credentials_source, credentials_data)


class IIFIClaimsClientPool(Interface):
    pass


class IFIClaimsClientPool(object):
    """
    IFI CLAIMS client pool as Pyramid utility implementation.
    """

# py27    implements(IIFIClaimsClientPool)

    def __init__(self, api_uri, api_uri_json):
        logger.info("Creating upstream client pool for IFI CLAIMS")
        self.api_uri = api_uri
        self.api_uri_json = api_uri_json
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPUnauthorized("Unable to discover credentials for IFI CLAIMS. identifier={}".format(identifier))

            if debug:
                logging.getLogger('oauthlib').setLevel(logging.DEBUG)

            logger.info("Creating upstream client for IFI CLAIMS. identifier={}".format(identifier))
            self.clients[identifier] = IFIClaimsClient(
                self.api_uri, self.api_uri_json, credentials['api_username'], credentials['api_password'])

        return self.clients.get(identifier)
