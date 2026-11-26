# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse
from patzilla.access.drawing import get_drawing_png
from patzilla.access.generic.pdf import pdf_universal, pdf_ziparchive
from patzilla.util.date import datetime_iso_filename, now
from patzilla.web.dependencies import CurrentUser, OpsClient, State, Vendor

log = logging.getLogger(__name__)

router = APIRouter(tags=["composite"])


@router.get("/api/drawing/{patent}", name="drawing", summary="Retrieve drawings for patent documents")
def drawing_handler(patent: str, client: OpsClient, page: int = 1):
    """request drawing, convert from tiff to png"""

    # TODO: respond with proper 4xx codes if something fails

    png = get_drawing_png(client, patent, page, 'FullDocumentDrawing')
    return Response(png, media_type='image/png')


@router.get("/api/pdf/{patent}", name="pdf", summary="Retrieve patent document PDF files")
def pdf_handler(patent: str, state: State, user: CurrentUser, vendor: Vendor):
    """request full document as pdf, universal datasource"""

    # The OPS client is optional, other data sources are tried first.
    client = state.client('ops', user=user, vendor=vendor)

    if ',' in patent:
        return pdf_serve_multi(client, patent)
    else:
        return pdf_serve_single(client, patent)


def pdf_serve_single(client, patent):

    # Acquire PDF document.
    data = pdf_universal(client, patent)

    if data.pdf is not None:
        # http://tools.ietf.org/html/rfc6266#section-4.2
        return Response(data.pdf, media_type='application/pdf', headers={
            'Content-Disposition': 'inline; filename={0}.pdf'.format(patent),
            'X-Pdf-Source': data.datasource,
        })

    elif data.meta:
        if 'location' in data.meta and data.meta['location']:
            url = data.meta['location']
            log.info('Redirecting PDF request to "{url}"'.format(url=url))
            return RedirectResponse(url, status_code=307)

    raise HTTPException(404, 'No PDF for document {patent}'.format(patent=patent))


def pdf_serve_multi(client, patents_raw):
    patents = patents_raw.split(',')
    patents = [patent.strip() for patent in patents]

    data = pdf_ziparchive(client, patents)
    zipfilename = 'ip-navigator-collection-pdf_{0}.zip'.format(datetime_iso_filename(now()))

    # http://tools.ietf.org/html/rfc6266#section-4.2
    return Response(data['zip'], media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename={0}'.format(zipfilename),
    })
