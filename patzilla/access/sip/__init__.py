# -*- coding: utf-8 -*-
# (c) 2014-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from pyramid.threadlocal import get_current_request

logger = logging.getLogger(__name__)

# ------------------------------------------
#   public interface
# ------------------------------------------
def get_sip_client():
    request = get_current_request()
    sip_client = request.sip_client
    logger.info('SIP request with username {0}'.format(sip_client.username))
    return sip_client
