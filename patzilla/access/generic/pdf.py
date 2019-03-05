# -*- coding: utf-8 -*-
# (c) 2013-2019 The PatZilla Developers
import logging
from StringIO import StringIO
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import attr
from pyramid.httpexceptions import HTTPError, HTTPNotFound
from patzilla.util.numbers.common import decode_patent_number
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.python import exception_traceback
from patzilla.access.dpma.depatisconnect import fetch_pdf as depatisconnect_fetch_pdf, NotConfiguredError
from patzilla.access.epo.ops.api import pdf_document_build as ops_build_pdf
from patzilla.access.epo.publicationserver.client import fetch_pdf as publicationserver_fetch_pdf
from patzilla.access.uspto.pdf import document_viewer_url as uspto_pdfview_url, fetch_pdf as uspto_fetch_pdf

log = logging.getLogger(__name__)


@attr.s
class PDFResponse(object):
    pdf = attr.ib(default=None)
    datasource = attr.ib(default=None)
    meta = attr.ib(default=attr.Factory(dict))
    success = attr.ib(default=False)


def pdf_universal(patent):
    """
    Attempt to fetch PDF document from best practice sources.

    It will progressively churn through these data sources:
    - EPO: European publication server
    - USPTO: Publication server
    - DPMA: DEPATISconnect
    - EPO: OPS services
    """

    # Create PDF response object.
    response = PDFResponse()

    # Acquire PDF document.
    try:
        response.success = pdf_universal_real(patent, response)

    except Exception as ex:
        log.warning('PDF acquisition for "%s" failed: %s', patent, ex)
        response.success = False

    return response


def pdf_universal_real(patent, response):

    document = decode_patent_number(patent)
    number_normalized = normalize_patent(patent)

    # Sanity checks.
    if document is None:
        log.error('Locating a document at the domestic office requires ' \
                  'a decoded document number for "{}"'.format(patent))
        raise ValueError(u'Unable to decode document number {}'.format(patent))

    # 1. If it's an EP document, try European publication server first.
    if response.pdf is None and document.country == 'EP':

        try:
            response.pdf = publicationserver_fetch_pdf(patent)
            response.datasource = 'epo-publication-server'

        except Exception as ex:
            log.warning('PDF {}: Not available from EPO. {}'.format(patent, ex))
            if not isinstance(ex, HTTPError):
                log.error(exception_traceback())

    # 2. Next, try USPTO servers if it's an US document.
    if response.pdf is None and document.country == 'US':

        try:
            response.pdf = uspto_fetch_pdf(patent)
            response.datasource = 'uspto'

        except Exception as ex:
            log.warning('PDF {}: Not available from USPTO. {}'.format(patent, ex))
            if not isinstance(ex, HTTPError):
                log.error(exception_traceback())

    # 3. Next, try DPMA servers.
    if response.pdf is None:
        try:
            # Skip requests for documents w/o kindcode
            if not document.kind:
                raise ValueError(u'No kindcode for patent: {}'.format(patent))

            response.pdf = depatisconnect_fetch_pdf(number_normalized)
            response.datasource = 'dpma'

        except Exception as ex:
            log.warning('PDF {}: Not available from DPMA. {}'.format(patent, ex))

            # Evaluate exception.
            if isinstance(ex, NotConfiguredError):
                log.warning(ex)

            elif not isinstance(ex, HTTPNotFound):
                log.error(exception_traceback())

    # 4. Next, try EPO OPS service.
    # Note this will assemble PDF out of single pages requested
    # from EPO OPS, which is a rather expensive operation.
    if response.pdf is None:

        # 2016-04-21: Amend document number for CA documents, e.g. CA2702893C -> CA2702893A1
        # TODO: Reenable feature, but only when prefixing document with a custom page
        #       informing the user about recent changes not yet arrived at EPO.
        # if document.country == 'CA':
        #    patent = document.country + document.number

        try:
            response.pdf = ops_build_pdf(patent)
            response.datasource = 'epo-ops'

        except Exception as ex:
            log.warning('PDF {}: Not available from OPS. {}'.format(patent, ex))
            if not isinstance(ex, HTTPError):
                log.error(exception_traceback())

    # 5. Last but not least, try to redirect to USPTO server.
    # TODO: Move elsewhere as deactivated on 2019-02-19.
    if False and response.pdf is None and document.country == 'US':

        log.info('PDF {}: USPTO attempt'.format(patent))
        uspto_found = False
        reason = None
        try:
            images_location = uspto_pdfview_url(document)
            if images_location:
                response.meta.update(images_location)
                response.datasource = 'uspto'
                uspto_found = True

        except Exception as ex:
            reason = ex
            if not isinstance(ex, HTTPError):
                log.error(exception_traceback())

        if not uspto_found:
            log.warning('PDF {}: Not available on USPTO. {}'.format(patent, reason))

    return True


def pdf_ziparchive(patents):
    buffer = StringIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        pdf_ziparchive_add(archive, patents)
    buffer.seek(0)
    payload = buffer.read()
    return {'zip': payload}


def pdf_ziparchive_add(zipfile, numbers, path=''):

    delivered = []
    missing = []

    for patent in numbers:

        # Skip empty numbers
        if not patent:
            continue

        log.info('PDF request for document {document}'.format(document=patent))
        try:
            data = pdf_universal(patent)
            if data.pdf is not None:
                inode = ZipInfo('{path}/{document}.pdf'.format(path=path, document=patent))
                zipfile.writestr(inode, data.pdf)
                delivered.append(patent)
            else:
                log.warning('No PDF for "{patent}" in context of a bulk request'.format(patent=patent))
                missing.append(patent)

        except HTTPError as ex:
            log.error('Problem fetching PDF for "{patent}" in context of a bulk request. error={ex}'.format(
                patent=patent, ex=ex))
            missing.append(patent)

    # TODO: Format more professionally incl. generator description
    # TODO: Unify with "Dossier.to_zip"
    report = \
        'Delivered files ({0}):\n'.format(len(delivered)) + '\n'.join(delivered) + \
        '\n\n' + \
        'Missing files ({0}):\n'.format(len(missing)) + '\n'.join(missing)
    zipfile.writestr('{path}/@report.txt'.format(path=path), report)
