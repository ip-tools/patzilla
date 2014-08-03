# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from elmyra.ip.access.dpma.depatisconnect import run_acquisition
from elmyra.ip.access.epo.ops import pdf_document_build
from elmyra.ip.access.epd.archive import fetch_pdf as archive_fetch_pdf

log = logging.getLogger(__name__)

def pdf_universal(patent):
    pdf = None
    datasource = None

    # first, try archive
    try:
        log.info('PDF - trying archive (1): {0}'.format(patent))
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
