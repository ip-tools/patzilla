# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
# Access IFI Claims Direct API
import logging
from pyramid.threadlocal import get_current_request

logger = logging.getLogger(__name__)

# ------------------------------------------
#   public interface
# ------------------------------------------
def get_ificlaims_client():
    request = get_current_request()
    client = request.ificlaims_client
    #logger.info('IFI Claims request with username {0}'.format(client.username))
    return client
