# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
from beaker.cache import cache_region
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.numbers.normalize import normalize_patent
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound
from elmyra.ip.access.epo.imageutil import tiff_to_png
from elmyra.ip.access.epo.ops import get_ops_image
from elmyra.ip.access.uspto.image import fetch_first_drawing as get_uspto_image

log = logging.getLogger(__name__)

@cache_region('static')
def get_drawing_png(document, page, kind):

    # try to fetch drawing from OPS, fall back to USPTO for US documents
    try:
        payload = get_ops_image(document, page, kind, 'tiff')
    except HTTPNotFound:
        if document.upper().startswith('US'):
            document_id = split_patent_number(document)
            document_id = normalize_patent(split_patent_number(document))
            payload = get_uspto_image(document_id)
        else:
            raise

    # croak if no image available
    if not payload:
        msg = 'No image available for document={document}, kind={kind}, page={page}'.format(**locals())
        log.warn(msg)
        raise HTTPNotFound(msg)

    # convert tiff to png
    try:
        payload = tiff_to_png(payload)
    except Exception as ex:
        raise HTTPInternalServerError(ex)

    return payload
