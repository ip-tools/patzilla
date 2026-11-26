# -*- coding: utf-8 -*-
# (c) 2019 The PatZilla Developers
import logging
from fastapi import APIRouter, Response
from patzilla.access.epo.publicationserver.client import fetch_pdf

log = logging.getLogger(__name__)

router = APIRouter(tags=["publicationserver"])


@router.get("/api/publicationserver/{patent}", name="publicationserver-pdf",
            summary="EPO publication server pdf interface")
def publicationserver_pdf_handler(patent: str):
    """request pdf from EPO publication server"""
    # https://data.epo.org/publication-server/pdf-document?cc=EP&pn=nnnnnn&ki=nn

    pdf_payload = fetch_pdf(patent)

    # http://tools.ietf.org/html/rfc6266#section-4.2
    return Response(pdf_payload, media_type='application/pdf', headers={
        'Content-Disposition': 'inline; filename={0}.pdf'.format(patent),
        'X-Pdf-Source': 'epo-publication-server',
    })
