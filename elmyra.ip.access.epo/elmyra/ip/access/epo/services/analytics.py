# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
from urllib import unquote_plus
from cornice.service import Service
from elmyra.ip.access.epo.ops import ops_analytics_applicant_family

log = logging.getLogger(__name__)

ops_analytics_applicant_family_service = Service(
    name='ops-analytics-applicant-family',
    path='/api/ops/analytics/applicant-family/{applicant}',
    renderer='prettyjson',
    description="OPS applicant-family analytics interface")

@ops_analytics_applicant_family_service.get()
def ops_analytics_applicant_family_handler(request):
    # TODO: respond with proper 4xx codes if something fails
    applicant = unquote_plus(request.matchdict['applicant'])
    response = ops_analytics_applicant_family(applicant)
    return response
