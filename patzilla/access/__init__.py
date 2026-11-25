# -*- coding: utf-8 -*-
# (c) 2017-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging

logger = logging.getLogger(__name__)


def setup(registry):

    datasources = []
    try:
        datasources = registry.application_settings.ip_navigator.datasources
        logger.info('Enabling data sources: {}'.format(datasources))
    except:
        logger.warning('No data source configured')

    if 'ops' in datasources:
        registry.include("patzilla.access.epo.ops.client")

    if 'depatisconnect' in datasources:
        registry.include("patzilla.access.dpma.depatisconnect")

    if 'ificlaims' in datasources:
        registry.include("patzilla.access.ificlaims.clientpool")

    if 'depatech' in datasources:
        registry.include("patzilla.access.depatech.clientpool")

    """
    if 'sip' in datasources:
        registry.include("patzilla.access.sip.concordance")
        registry.include("patzilla.access.sip.clientpool")
    """

    registry.include("patzilla.access.office")
