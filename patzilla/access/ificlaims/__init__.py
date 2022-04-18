# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from pyramid.httpexceptions import HTTPBadGateway
from pyramid.threadlocal import get_current_request

logger = logging.getLogger(__name__)


def get_ificlaims_client():
    """
    Get a managed client for accessing the IFI CLAIMS Direct API.
    """
    request = get_current_request()

    if hasattr(request, 'ificlaims_client'):
        client = request.ificlaims_client
        logger.debug("IFI CLAIMS request with username: {}".format(client.username))
        return client
    else:
        raise HTTPBadGateway("IFI CLAIMS: Data source not enabled or not configured")
