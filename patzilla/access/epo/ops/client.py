# -*- coding: utf-8 -*-
# (c) 2014-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import os

import epo_ops
from mock import mock
from starlette.exceptions import HTTPException

from patzilla.access.generic.credentials import AbstractCredentialsGetter

logger = logging.getLogger(__name__)


def create_pool(datasource_settings, metrics_manager=None):
    return OpsClientPool(metrics_manager=metrics_manager)


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
        if not os.environ["OPS_API_CONSUMER_KEY"] or not os.environ["OPS_API_CONSUMER_SECRET"]:
            raise KeyError("One of the OPS credential environment variable is set but empty")
        return {
            "consumer_key": os.environ["OPS_API_CONSUMER_KEY"],
            "consumer_secret": os.environ["OPS_API_CONSUMER_SECRET"],
        }


class OpsClientPool:
    """
    EPO/OPS client pool, holding one client per credentials context.
    """

    def __init__(self, metrics_manager=None):
        logger.info("Creating upstream client pool for EPO/OPS")
        self.metrics_manager = metrics_manager
        self.clients = {}

    def get(self, identifier, credentials=None):
        if identifier not in self.clients:
            if credentials is None:
                raise HTTPException(401, "Unable to discover credentials for EPO OPS. identifier={}".format(identifier))
            logger.info("Creating upstream client for EPO/OPS. identifier={}".format(identifier))
            self.clients[identifier] = ops_client_factory(
                key=credentials['consumer_key'], secret=credentials['consumer_secret'], metrics_manager=self.metrics_manager)

        return self.clients.get(identifier)


def ops_client_factory(key, secret, metrics_manager=None):

    # TODO: Enable throttling and caching.
    ops = epo_ops.Client(
        key=key, secret=secret,
        accept_type='json', middlewares=[]
    )

    # Attach metrics manager object to ops client instance.
    ops.metrics_manager = metrics_manager or mock.Mock()  # ty: ignore[unresolved-attribute]

    return ops


class UserBoundClient:
    """
    Delegates to a shared, pooled API client, carrying the id of the requesting user for usage accounting.
    """

    def __init__(self, client, userid=None):
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "userid", userid)

    def __getattr__(self, name):
        return getattr(self._client, name)

    def __setattr__(self, name, value):
        setattr(self._client, name, value)
