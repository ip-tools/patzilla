# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from StringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
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

        # third, try building from OPS single images
        except:
            log.info('PDF - trying OPS: {0}'.format(patent))
            pdf = pdf_document_build(patent)
            datasource = 'ops'

    return {'pdf': pdf, 'datasource': datasource}

def pdf_universal_multi(patents):
    buffer = StringIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        for patent in patents:
            data = pdf_universal(patent)
            if data.get('pdf'):
                archive.writestr('{0}.pdf'.format(patent), data['pdf'])

    buffer.seek(0)
    payload = buffer.read()

    return {'zip': payload}
