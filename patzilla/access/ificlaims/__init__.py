# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
# Access IFI CLAIMS Direct API
import logging
from pyramid.httpexceptions import HTTPBadGateway
from pyramid.threadlocal import get_current_request

logger = logging.getLogger(__name__)

# ------------------------------------------
#   public interface
# ------------------------------------------
def get_ificlaims_client():
    request = get_current_request()

    if hasattr(request, 'ificlaims_client'):
        client = request.ificlaims_client
        #logger.info('IFI CLAIMS request with username {0}'.format(client.username))
        return client
    else:
        raise HTTPBadGateway('Datasource "ificlaims" not configured.')
