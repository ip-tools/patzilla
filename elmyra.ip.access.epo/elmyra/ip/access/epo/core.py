# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
from StringIO import StringIO
import logging
from zipfile import ZipFile, ZIP_DEFLATED
from elmyra.ip.access.dpma.depatisconnect import run_acquisition
from elmyra.ip.access.epo.ops import pdf_document_build
from elmyra.ip.access.epd.archive import fetch_pdf as archive_fetch_pdf

log = logging.getLogger(__name__)

def pdf_universal(patent):
    pdf = None
    datasource = None

    # first, try archive
    try:
        pdf = archive_fetch_pdf(patent)
        datasource = 'archive'
    except:

        # second, try archive again after running acquisition
        try:
            log.info('PDF - trying archive (2): {0}'.format(patent))
            run_acquisition(patent, 'pdf')
            pdf = archive_fetch_pdf(patent)
            datasource = 'archive'

        # third, try building from OPS single images
        except:
            log.info('PDF - trying OPS: {0}'.format(patent))
            pdf = pdf_document_build(patent)
            datasource = 'ops'
            pass

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
