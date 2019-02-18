# -*- coding: utf-8 -*-
# (c) 2019 The PatZilla Developers
import logging
from cornice.service import Service
from patzilla.access.epo.publicationserver.client import fetch_pdf

log = logging.getLogger(__name__)


publicationserver_pdf_service = Service(
    name='publicationserver-pdf',
    path='/api/publicationserver/{patent}',
    description="EPO publication server pdf interface")


@publicationserver_pdf_service.get(renderer='pdf')
def publicationserver_pdf_handler(request):
    """request pdf from EPO publication server"""
    # https://data.epo.org/publication-server/pdf-document?cc=EP&pn=nnnnnn&ki=nn

    patent = request.matchdict['patent']

    pdf_payload = fetch_pdf(patent)

    # http://tools.ietf.org/html/rfc6266#section-4.2
    request.response.headers['Content-Disposition'] = 'inline; filename={0}.pdf'.format(patent)
    request.response.headers['X-Pdf-Source'] = 'epo-publication-server'

    return pdf_payload
