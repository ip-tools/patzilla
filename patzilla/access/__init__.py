# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging

logger = logging.getLogger(__name__)


def includeme(config):

    datasources = []
    try:
        datasources = config.registry.application_settings.ip_navigator.datasources
        logger.info('Enabling data sources: {}'.format(datasources))
    except:
        logger.warning('No data source configured')

    if 'ops' in datasources:
        config.include("patzilla.access.epo.ops.client")

    if 'depatisconnect' in datasources:
        config.include("patzilla.access.dpma.depatisconnect")

    if 'ificlaims' in datasources:
        config.include("patzilla.access.ificlaims.clientpool")

    if 'depatech' in datasources:
        config.include("patzilla.access.depatech.clientpool")

    """
    if 'sip' in datasources:
        config.include("patzilla.access.sip.concordance")
        config.include("patzilla.access.sip.clientpool")
    """

    config.include('.office')
