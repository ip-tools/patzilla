# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import logging
from cornice.service import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from patzilla.access.drawing import get_drawing_png
from patzilla.access.generic.pdf import pdf_universal, pdf_ziparchive
from patzilla.util.date import datetime_iso_filename, now

log = logging.getLogger(__name__)

drawing_service = Service(
    name='drawing',
    path='/api/drawing/{patent}',
    description="Retrieve drawings for patent documents")

pdf_service = Service(
    name='pdf',
    path='/api/pdf/{patent}',
    description="Retrieve patent document PDF files")


@drawing_service.get(renderer='png')
def drawing_handler(request):
    """request drawing, convert from tiff to png"""

    # TODO: respond with proper 4xx codes if something fails

    patent = request.matchdict['patent']
    page = int(request.params.get('page', 1))
    png = get_drawing_png(patent, page, 'FullDocumentDrawing')
    return png


@pdf_service.get(renderer='null')
def pdf_handler(request):
    """request full document as pdf, universal datasource"""

    if ',' in request.matchdict['patent']:
        return pdf_serve_multi(request)
    else:
        return pdf_serve_single(request)


def pdf_serve_single(request):

    patent = request.matchdict['patent']
    #parts = request.matchdict['parts']

    # Acquire PDF document.
    data = pdf_universal(patent)

    if data.pdf is not None:
        # http://tools.ietf.org/html/rfc6266#section-4.2
        request.response.content_type = 'application/pdf'
        request.response.charset = None
        request.response.headers['Content-Disposition'] = 'inline; filename={0}.pdf'.format(patent)
        request.response.headers['X-Pdf-Source'] = data.datasource
        return data.pdf

    elif data.meta:
        if 'location' in data.meta and data.meta['location']:
            url = data.meta['location']
            log.info('Redirecting PDF request to "{url}"'.format(url=url))
            raise HTTPTemporaryRedirect(location=url)

    raise HTTPNotFound('No PDF for document {patent}'.format(patent=patent))


def pdf_serve_multi(request):
    patents_raw = request.matchdict['patent']
    patents = patents_raw.split(',')
    patents = [patent.strip() for patent in patents]

    data = pdf_ziparchive(patents)
    zipfilename = 'ip-navigator-collection-pdf_{0}.zip'.format(datetime_iso_filename(now()))

    # http://tools.ietf.org/html/rfc6266#section-4.2
    request.response.content_type = 'application/zip'
    request.response.charset = None
    request.response.headers['Content-Disposition'] = 'attachment; filename={0}'.format(zipfilename)
    return data['zip']
