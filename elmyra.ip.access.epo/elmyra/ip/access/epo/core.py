# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import logging
from StringIO import StringIO
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from pyramid.httpexceptions import HTTPError
from elmyra.ip.access.uspto.image import get_images_view_url
from elmyra.ip.util.numbers.common import decode_patent_number
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.access.dpma.depatisconnect import run_acquisition, fetch_pdf as archive_fetch_pdf
from elmyra.ip.access.epo.ops import pdf_document_build

log = logging.getLogger(__name__)

def pdf_universal(patent):

    pdf = None
    datasource = None
    meta = {}

    document = decode_patent_number(patent)
    number_normalized = normalize_patent(patent)

    # first, try archive
    try:
        # Skip requests for documents w/o kindcode
        if not document.kind: raise ValueError(u'No kindcode')
        log.info('PDF - trying archive (1): {0}'.format(number_normalized))

        pdf = archive_fetch_pdf(number_normalized)
        datasource = 'archive'

    except:

        # second, try archive again after running acquisition
        try:

            # Skip requests for documents w/o kindcode
            if not document.kind: raise ValueError(u'No kindcode')

            log.info('PDF - trying archive (2): {0}'.format(number_normalized))

            run_acquisition(number_normalized, 'pdf')
            pdf = archive_fetch_pdf(number_normalized)
            datasource = 'archive'

        except:

            if document:

                # third, try building from OPS single images
                try:

                    # 2016-04-21: Amend document number for CA documents, e.g. CA2702893C -> CA2702893A1
                    # TOOD: Reenable feature, but only when prefixing document with a custom page
                    #       informing the user about recent changes not yet arrived at EPO.
                    #if document.country == 'CA':
                    #    patent = document.country + document.number

                    log.info('PDF - trying OPS: {0}'.format(patent))

                    pdf = pdf_document_build(patent)
                    datasource = 'ops'

                except:
                    if document.country == 'US':

                        log.info('PDF - trying to redirect to external data source: {0}'.format(patent))
                        images_location = get_images_view_url(document)
                        if images_location:
                            meta.update(images_location)
                        else:
                            log.warning('PDF - not available at USPTO: {}'.format(patent))

            else:
                log.error('Locating a document at the domestic office requires ' \
                          'a decoded document number for "{}"'.format(patent))

    return {'pdf': pdf, 'datasource': datasource, 'meta': meta}

def pdf_universal_multi_zip(patents):
    buffer = StringIO()
    with ZipFile(buffer, 'w', ZIP_DEFLATED) as archive:
        pdf_universal_multi(archive, patents)
    buffer.seek(0)
    payload = buffer.read()
    return {'zip': payload}

def pdf_universal_multi(zipfile, patents, path=''):

    delivered = []
    missing = []

    #inode = ZipInfo('{path}/'.format(path=path))
    #zipfile.writestr(inode, '')

    for patent in patents:
        try:
            data = pdf_universal(patent)
            if 'pdf' in data and data['pdf']:
                inode = ZipInfo('{path}/{document}.pdf'.format(path=path, document=patent))
                zipfile.writestr(inode, data['pdf'])
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

