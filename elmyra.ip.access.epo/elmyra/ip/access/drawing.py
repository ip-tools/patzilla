# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import logging
from beaker.cache import cache_region
from pyramid.httpexceptions import HTTPInternalServerError, HTTPNotFound
from elmyra.ip.util.numbers.common import split_patent_number
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.access.epo.imageutil import to_png
from elmyra.ip.access.epo.ops import get_ops_image
from elmyra.ip.access.uspto.image import fetch_first_drawing as get_uspto_image
from elmyra.ip.access.cipo.drawing import fetch_first_drawing as get_cipo_image

log = logging.getLogger(__name__)

@cache_region('longer')
def get_drawing_png(document, page, kind):

    # 2. Try to fetch drawing from OPS, fall back to other patent offices
    try:
        payload = get_ops_image(document, page, kind, 'tiff')

    except HTTPNotFound:

        # fallback to USPTO (U.S.)
        if document.upper().startswith('US'):
            #document_id = split_patent_number(document)
            document_id = normalize_patent(split_patent_number(document))
            try:
                payload = get_uspto_image_cached(document_id)
            except PayloadEmpty as ex:
                raise HTTPNotFound('No drawing for "{0}" at OPS or USPTO'.format(document))

        # fallback to CIPO (Canada)
        elif document.upper().startswith('CA'):
            document_id = split_patent_number(document)
            try:
                payload = get_cipo_image_cached(document_id)
            except PayloadEmpty as ex:
                raise HTTPNotFound('No drawing for "{0}" at OPS or CIPO'.format(document))

        # otherwise, pass through exception
        else:
            raise

    # 3. Croak if no image available
    if not payload:
        msg = 'No image available for document={document}, kind={kind}, page={page}'.format(**locals())
        log.warn(msg)
        raise HTTPNotFound(msg)

    # 4. Convert image from TIFF to PNG format
    payload = to_png(payload, format='tif')

    return payload

class PayloadEmpty(Exception):
    pass

@cache_region('longer')
def get_uspto_image_cached(document_id):
    payload = get_uspto_image(document_id)
    if payload:
        return payload
    else:
        raise PayloadEmpty('No payload')

@cache_region('longer')
def get_cipo_image_cached(document_id):
    payload = get_cipo_image(document_id)
    if payload:
        return payload
    else:
        raise PayloadEmpty('No payload')
