# -*- coding: utf-8 -*-
# (c) 2017-2026 Andreas Motl <andreas.motl@ip-tools.org>
import logging

from patzilla.access.generic.credentials import DatasourceCredentialsManager
from patzilla.util.config import read_list

logger = logging.getLogger(__name__)


def create_pools(global_settings, metrics_manager=None):
    """
    Create upstream client pools for all configured data sources, keyed by data source name.
    """
    from patzilla.access.depatech import clientpool as depatech
    from patzilla.access.dpma import depatisconnect
    from patzilla.access.epo.ops import client as ops
    from patzilla.access.ificlaims import clientpool as ificlaims

    datasource_settings = global_settings.datasource_settings
    datasources = read_list(global_settings.application_settings.get('ip_navigator', {}).get('datasources'))
    if datasources:
        logger.info('Enabling data sources: {}'.format(datasources))
    else:
        logger.warning('No data source configured')

    pools = {}
    if 'ops' in datasources:
        pools['ops'] = ops.create_pool(datasource_settings, metrics_manager=metrics_manager)
    if 'depatisconnect' in datasources:
        depatisconnect.configure(datasource_settings)
    if 'ificlaims' in datasources:
        pools['ificlaims'] = ificlaims.create_pool(datasource_settings)
    if 'depatech' in datasources:
        pools['depatech'] = depatech.create_pool(datasource_settings)
    return {name: pool for name, pool in pools.items() if pool is not None}


def credentials_getter(datasource):
    from patzilla.access.depatech.clientpool import DepaTechCredentialsGetter
    from patzilla.access.epo.ops.client import OpsCredentialsGetter
    from patzilla.access.ificlaims.clientpool import IfiClaimsCredentialsGetter
    from patzilla.access.sip.clientpool import SipCredentialsGetter
    return {
        'ops': OpsCredentialsGetter,
        'ificlaims': IfiClaimsCredentialsGetter,
        'depatech': DepaTechCredentialsGetter,
        'sip': SipCredentialsGetter,
    }[datasource]


def resolve_client(pools, datasource, datasource_settings, user=None, vendor=None):
    """
    Return the upstream client for a data source, using the credentials of the
    user, vendor, or system, in this order. Returns `None` when not available.
    """
    pool = pools.get(datasource)
    if pool is None:
        return None
    manager = DatasourceCredentialsManager(identifier=datasource, credentials_getter=credentials_getter(datasource))
    try:
        source, credentials = manager.resolve(user=user, vendor=vendor, datasource_settings=datasource_settings)
    except Exception:
        logger.exception("Unable to resolve credentials for data source: {}".format(datasource))
        return None
    return pool.get(source, credentials)
