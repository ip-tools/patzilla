# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import logging
from StringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from pyramid.httpexceptions import HTTPError, HTTPTemporaryRedirect
from elmyra.ip.util.numbers.common import decode_patent_number
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.access.dpma.depatisconnect import run_acquisition, fetch_pdf as archive_fetch_pdf
from elmyra.ip.access.epo.ops import pdf_document_build

log = logging.getLogger(__name__)

def pdf_universal(patent):
    pdf = None
    datasource = None

    number_normalized = normalize_patent(patent)

    # first, try archive
    try:
        log.info('PDF - trying archive (1): {0}'.format(number_normalized))
        pdf = archive_fetch_pdf(number_normalized)
        datasource = 'archive'
    except:

        # second, try archive again after running acquisition
        try:
            log.info('PDF - trying archive (2): {0}'.format(number_normalized))
            run_acquisition(number_normalized, 'pdf')
            pdf = archive_fetch_pdf(number_normalized)
            datasource = 'archive'

        except:

            # third, try building from OPS single images
            try:
                log.info('PDF - trying OPS: {0}'.format(patent))
                pdf = pdf_document_build(patent)
                datasource = 'ops'
            except:
                log.info('PDF - trying to redirect to external datasource: {0}'.format(patent))
                reference_type = None
                document = decode_patent_number(patent)
                if document.country == 'US':
                    if len(document.number) <= 9:
                        reference_type = 'publication'
                    elif len(document.number) >= 10:
                        reference_type = 'application'

                url_tpl = None
                if reference_type == 'application':
                    # AppFT image server
                    # http://pdfaiw.uspto.gov/.aiw?docid=20160105912
                    url_tpl = 'http://pdfaiw.uspto.gov/.aiw?docid={docid}'

                elif reference_type == 'publication':
                    # PatFT image server
                    # http://pdfpiw.uspto.gov/.piw?docid=9317610
                    url_tpl = 'http://pdfpiw.uspto.gov/.piw?docid={docid}'

                if url_tpl:
                    url = url_tpl.format(docid=document.number)
                    log.info('PDF - redirecting to "{0}"'.format(url))
                    raise HTTPTemporaryRedirect(location=url)

    return {'pdf': pdf, 'datasource': datasource}

def pdf_universal_multi(patents):
    buffer = StringIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:

        delivered = []
        missing = []
        for patent in patents:
            try:
                data = pdf_universal(patent)
                if data.get('pdf'):
                    archive.writestr('{0}.pdf'.format(patent), data['pdf'])
                    delivered.append(patent)
            except HTTPError as ex:
                missing.append(patent)

        # TODO: format more professionally incl. generator description
        report = \
            'Delivered PDF files ({0}):\n'.format(len(delivered)) + '\n'.join(delivered) + \
            '\n\n' + \
            'Missing PDF files ({0}):\n'.format(len(missing)) + '\n'.join(missing)
        archive.writestr('report.txt', report)

    buffer.seek(0)
    payload = buffer.read()

    return {'zip': payload}
