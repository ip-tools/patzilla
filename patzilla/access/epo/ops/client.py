# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

import epo_ops
from mock import mock
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.threadlocal import get_current_registry
from zope.interface.declarations import implements
from zope.interface.interface import Interface
from zope.interface.interfaces import ComponentLookupError

from patzilla.access.generic.credentials import AbstractCredentialsGetter, DatasourceCredentialsManager
from patzilla.util.web.identity.store import IUserMetricsManager

logger = logging.getLogger(__name__)


def includeme(config):
    config.registry.registerUtility(OpsClientPool())
    config.add_subscriber(attach_ops_client, "pyramid.events.ContextFound")


class OpsCredentialsGetter(AbstractCredentialsGetter):
    """
    Define how to acquire EPO/OPS credentials from
    configuration settings or environment variables.
    """

    @staticmethod
    def from_settings(datasource_settings):
        datasource = datasource_settings.datasource
        return {
            'consumer_key': datasource.ops.api_consumer_key,
            'consumer_secret': datasource.ops.api_consumer_secret,
        }

    @staticmethod
    def from_environment():
        return {
            "consumer_key": os.environ["OPS_API_CONSUMER_KEY"],
            "consumer_secret": os.environ["OPS_API_CONSUMER_SECRET"],
        }


def attach_ops_client(event):
    """
    Create EPO/OPS client pool per credentials context.
    """

    # Don't start data source machinery on requests to static assets.
    if '/static' in event.request.url:
        return

    request = event.request

    try:
        dcm = DatasourceCredentialsManager(identifier="ops", credentials_getter=OpsCredentialsGetter)
        credentials_source, credentials_data = dcm.resolve(request)
    except:
        logger.exception("Unable to resolve credentials for OPS")
        return

    ckshort = credentials_data['consumer_key'][:10] + "..."
    logger.debug('Attaching OPS credentials from "{}": {}'.format(credentials_source, ckshort))

    pool = request.registry.getUtility(IOpsClientPool)
    request.ops_client = pool.get(credentials_source, credentials_data)


class IOpsClientPool(Interface):
    pass


class OpsClientPool(object):
    """
    EPO/OPS client pool as Pyramid utility implementation.
    """

    implements(IOpsClientPool)

    def __init__(self):
        logger.info("Creating upstream client pool for EPO/OPS")
        self.clients = {}

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            if credentials is None:
                raise HTTPUnauthorized("Unable to discover credentials for EPO OPS. identifier={}".format(identifier))
            logger.info("Creating upstream client for EPO/OPS. identifier={}".format(identifier))
            self.clients[identifier] = ops_client_factory(key=credentials['consumer_key'], secret=credentials['consumer_secret'])

        return self.clients.get(identifier)


def ops_client_factory(key, secret):

    # TODO: Enable throttling and caching.
    ops = epo_ops.Client(
        key=key, secret=secret,
        accept_type='json', middlewares=[]
    )

    # Attach metrics manager object to ops client instance.
    registry = get_current_registry()
    try:
        ops.metrics_manager = registry.getUtility(IUserMetricsManager)
    except ComponentLookupError:
        ops.metrics_manager = mock.Mock()

    return ops
