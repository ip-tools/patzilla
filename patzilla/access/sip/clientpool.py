# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

from pyramid.httpexceptions import HTTPUnauthorized
from zope.interface import implementer
from zope.interface.interface import Interface
from zope.interface import implementer

from patzilla.access.generic.credentials import AbstractCredentialsGetter, DatasourceCredentialsManager
from patzilla.access.sip.client import SipClient

logger = logging.getLogger(__name__)


def includeme(config):

    # Acquire settings for SIP.
    datasource_settings = config.registry.datasource_settings
    sip_settings = datasource_settings.datasource.sip

    # Get URI settings, optionally falling back to environment variables.
    api_uri = sip_settings.get("api_uri", os.environ.get("SIP_API_URI"))

    # When an API URI can be discovered, register the component.
    if api_uri:
        logger.info("Using SIP API at {}".format(api_uri))
        config.registry.registerUtility(SipClientPool(api_uri=api_uri))
        config.add_subscriber(attach_sip_client, "pyramid.events.ContextFound")


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


def attach_sip_client(event):
    """
    Create SIP client pool per credentials context.
    """

    # Don't start data source machinery on requests to static assets.
    if '/static' in event.request.url:
        return

    request = event.request

    try:
        dcm = DatasourceCredentialsManager(identifier="sip", credentials_getter=SipCredentialsGetter)
        credentials_source, credentials_data = dcm.resolve(request)
    except:
        logger.exception("Unable to resolve credentials for SIP")
        return

    username = credentials_data['api_username'][:10]
    logger.debug('Attaching SIP credentials from "{}": {}'.format(credentials_source, username))

    pool = request.registry.getUtility(ISipClientPool)
    request.sip_client = pool.get(credentials_source, credentials_data)


class ISipClientPool(Interface):
    pass


@implementer(ISipClientPool)
class SipClientPool(object):
    """
    SIP client pool as Pyramid utility implementation.
    """

    def __init__(self, api_uri):
        logger.info("Creating upstream client pool for SIP")
        self.api_uri = api_uri
        self.clients = {}

    def get(self, identifier, credentials=None, debug=False):
        if identifier not in self.clients:

            if credentials is None:
                raise HTTPUnauthorized("Unable to discover credentials for SIP. identifier={}".format(identifier))

            logger.info("Creating upstream client for SIP. identifier={}".format(identifier))
            self.clients[identifier] = SipClient(
                uri=self.api_uri, username=credentials['api_username'], password=credentials['api_password'])

        return self.clients.get(identifier)

