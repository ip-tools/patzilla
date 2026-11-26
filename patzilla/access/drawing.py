# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
from six import BytesIO
from beaker.cache import cache_region
from starlette.exceptions import HTTPException

from patzilla.access.generic.exceptions import is_http_error
from patzilla.boot.cache import client_cache_region
from patzilla.util.numbers.common import split_patent_number
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.image.convert import to_png
from patzilla.access.epo.ops.api import get_ops_image
from patzilla.access.uspto.image import fetch_first_drawing as get_uspto_image
from patzilla.access.cipo.drawing import fetch_first_drawing as get_cipo_image

log = logging.getLogger(__name__)

# TODO: Refactor to patzilla.access.composite.drawing

@client_cache_region('longer')
def get_drawing_png(client, document, page, kind):

    # 2. Try to fetch drawing from OPS, fall back to other patent offices
    try:
        payload = get_ops_image(client, document, page, kind, 'tiff')

    except Exception as ex:
        if not is_http_error(ex, 404):
            raise

        # fallback to USPTO (U.S.)
        if document.upper().startswith('US'):
            document_id = normalize_patent(split_patent_number(document), for_ops=False)
            try:
                payload = get_uspto_image_cached(document_id)
            except PayloadEmpty as ex:
                raise HTTPException(404, 'No drawing for "{0}" at OPS or USPTO'.format(document))

        # fallback to CIPO (Canada)
        elif document.upper().startswith('CA'):
            document_id = split_patent_number(document)
            try:
                payload = get_cipo_image_cached(document_id)
            except PayloadEmpty as ex:
                raise HTTPException(404, 'No drawing for "{0}" at OPS or CIPO'.format(document))

        # otherwise, pass through exception
        else:
            raise

    # 3. Croak if no image available
    if not payload:
        msg = 'No image available for document={document}, kind={kind}, page={page}'.format(**locals())
        log.warning(msg)
        raise HTTPException(404, msg)

    # 4. Convert image from TIFF to PNG format
    payload = to_png(BytesIO(payload))

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
