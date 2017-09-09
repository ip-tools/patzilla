# -*- coding: utf-8 -*-
# (c) 2017 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
# Access MTC depa.tech API
import logging
from pyramid.httpexceptions import HTTPBadGateway
from pyramid.threadlocal import get_current_request

logger = logging.getLogger(__name__)

# ------------------------------------------
#   public interface
# ------------------------------------------
def get_depatech_client():
    request = get_current_request()
    if hasattr(request, 'depatech_client'):
        client = request.depatech_client
        #logger.info('depa.tech request with username {0}'.format(client.username))
        return client
    else:
        raise HTTPBadGateway('Datasource "depatech" not configured.')

