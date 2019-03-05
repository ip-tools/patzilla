# -*- coding: utf-8 -*-
# (c) 2013-2019 Andreas Motl <andreas.motl@ip-tools.org>
import time
import logging
from pprint import pformat
from contextlib import contextmanager

import epo_ops
from cornice.util import json_error, to_list
from beaker.cache import cache_region
from simplejson.scanner import JSONDecodeError
from jsonpointer import JsonPointer, resolve_pointer, set_pointer, JsonPointerException
from pyramid.threadlocal import get_current_request
from pyramid.httpexceptions import HTTPNotFound, HTTPError, HTTPBadRequest, HTTPBadGateway
from patzilla.navigator.util import object_attributes_to_dict
from patzilla.util.image.convert import pdf_join, pdf_set_metadata, pdf_make_metadata
from patzilla.access.generic.exceptions import NoResultsException
from patzilla.util.numbers.common import decode_patent_number, split_patent_number

log = logging.getLogger(__name__)


OPS_API_URI         = 'https://ops.epo.org/3.2/rest-services'
OPS_AUTH_URI        = 'https://ops.epo.org/3.2/auth'
OPS_DEVELOPERS_URI  = 'https://ops.epo.org/3.2/developers'

# values of these indexes will be considered keywords
ops_keyword_fields = [

    # OPS
    'title', 'ti',
    'abstract', 'ab',
    'titleandabstract', 'ta',
    'txt',
    'applicant', 'pa',
    'inventor', 'in',
    'inventorandapplicant', 'ia',

    'ct', 'citation',

    # classifications
    'ipc', 'ic',
    'cpc', 'cpci', 'cpca', 'cl',

    # application and priority
    'ap', 'applicantnumber', 'sap',
    'pr', 'prioritynumber', 'spr',

]


def get_ops_client():
    request = get_current_request()
    ops_client = request.ops_client
    log.debug('OPS request with client-id {0}'.format(ops_client.key))
    return ops_client


@contextmanager
def ops_client(xml=False):

    # FIXME: Better use "accept_type" on a per-request basis supported by ``python-epo-ops-client``.

    # Acquire OPS client instance.
    ops = get_ops_client()

    try:
        # Conditionally switch to XML.
        if xml:
            ops.accept_type = 'application/xml'
        yield ops

    # Reset to default content type.
    finally:
        ops.accept_type = 'application/json'


@cache_region('search', 'ops_search')
def ops_published_data_search_swap_family(constituents, query, range):
    results = ops_published_data_search(constituents, query, range)
    #pprint(results)
    numbers = results_swap_family_members(results)
    #pprint(numbers)
    return results


def results_swap_family_members(response):

    #pointer_results = JsonPointer('/ops:world-patent-data/ops:biblio-search/ops:search-result/ops:publication-reference')
    #entries = pointer_results.resolve(results)

    publication_numbers = []

    # DE, EP..B, WO, EP..A2, EP..A3, EP, US
    priorities = [
        {'filter': lambda patent: patent.country.startswith('DE') and not patent.kind.startswith('D1')},
        {'filter': lambda patent: patent.country.startswith('EP') and patent.kind.startswith('B')},
        {'filter': 'WO'},
        {'filter': lambda patent: patent.country.startswith('EP') and patent.kind.startswith('A')},
        {'filter': 'EP'},
        {'filter': 'US'},
    ]

    def match_filter(item, filter):
        if callable(filter):
            patent = split_patent_number(item)
            outcome = filter(patent)
        else:
            outcome = item.startswith(filter)
        return outcome

    pointer_results = JsonPointer('/ops:world-patent-data/ops:biblio-search/ops:search-result/exchange-documents')
    pointer_publication_reference = JsonPointer('/bibliographic-data/publication-reference/document-id')
    #pointer_publication_reference = JsonPointer('/exchange-document/bibliographic-data/publication-reference/document-id')

    # A.1 compute distinct list with unique families
    family_representatives = {}
    chunks = to_list(pointer_results.resolve(response))
    all_results = []
    for chunk in chunks:

        #print 'chunk:', chunk

        # Prepare list of document cycles
        #chunk_results = to_list(pointer_publication_reference.resolve(chunk))
        cycles = to_list(chunk['exchange-document'])

        # Publication number of first cycle in EPODOC format
        representation = cycles[0]
        pubref = pointer_publication_reference.resolve(representation)
        representation_pubref_epodoc, _ = _get_document_number_date(pubref, 'epodoc')

        # All publication numbers in DOCDB format
        representation_pubrefs_docdb = []
        for cycle in cycles:
            pubref = pointer_publication_reference.resolve(cycle)
            representation_pubref_docdb, _ = _get_document_number_date(pubref, 'docdb')
            representation_pubrefs_docdb.append(representation_pubref_docdb)

        # Debugging
        #print 'representation_pubref_epodoc:', representation_pubref_epodoc
        #print 'representation_pubrefs_docdb:', representation_pubrefs_docdb

        # Fetch family members. When failing, use first cycle as representation.
        try:
            family_info = ops_family_members(representation_pubref_epodoc)
        except:
            log.warning('Failed to fetch family information for %s', representation_pubref_epodoc)
            chunk['exchange-document'] = representation
            request = get_current_request()
            del request.errors[:]
            continue

        #members = family_info.publications_by_country()
        #pprint(members)

        # Find replacement from list of family members controlled by priority list.
        for prio in priorities:

            filter = prio['filter']

            # Debugging
            #print 'checking prio:', filter

            if match_filter(representation_pubref_epodoc, filter):
                break

            bibdata = None
            found = False
            for member in family_info.items:

                # Debugging
                #print 'member:'; pprint(member)

                member_pubnum = member['publication']['number-docdb']

                if match_filter(member_pubnum, filter):

                    # Debugging
                    #print 'Filter matched for member:', member_pubnum

                    try:
                        bibdata = ops_biblio_documents(member_pubnum)
                    except:
                        #log.warning('Fetching bibliographic data failed for %s', member_pubnum)
                        request = get_current_request()
                        del request.errors[:]
                        continue

                    #pprint(bibdata)
                    if bibdata:

                        # TODO: Add marker that this document was swapped, display appropriately.
                        found = True
                        break

            # Swap representation of document by appropriate family member
            # and set a marker in the data structure containing the original
            # document number(s).
            if found:

                representation = bibdata
                #print 'representation:'; pprint(representation)

                representation[0].setdefault('__meta__', {})
                representation[0]['__meta__']['swapped'] = {
                    'canonical': representation_pubrefs_docdb[0],
                    'list': [representation_pubref_epodoc] + representation_pubrefs_docdb,
                    }

                break

        # TODO: Here, duplicate documents might be. Prune/deduplicate them.
        # TODO: When choosing german family members (e.g. for EP666666), abstract is often missing.
        # TODO: => Carry along from original representation.

        """
        for result in cycles:
            #pprint(result)
            pubref = pointer_publication_reference.resolve(result)
            #print entry, pubref
            pubref_number, pubref_date = _get_document_number_date(pubref, 'docdb')
            publication_numbers.append(pubref_number)
        """

        chunk['exchange-document'] = representation

    # Filter duplicates
    seen = []
    results = []
    fields = ['@country', '@doc-number', '@kind', '@family-id']
    for chunk in chunks:

        # Prepare list of document cycles.
        cycles = to_list(chunk['exchange-document'])

        # Only look at first cycle slot.
        doc = cycles[0]

        # Compute unique document identifier.
        ident = {}
        for key in fields:
            ident[key] = doc[key]

        # Collect chunk if not seen yet.
        if ident in seen:
            continue
        else:
            seen.append(ident)
            results.append(chunk)

    # Overwrite reduced list of chunks in original DOM.
    pointer_results.set(response, results)

    return publication_numbers


@cache_region('search', 'ops_search')
def ops_published_data_search(constituents, query, range):
    return ops_published_data_search_real(constituents, query, range)


def ops_published_data_search_real(constituents, query, range):

    # OPS client object, impersonated for the current user.
    ops = get_ops_client()

    # Send request to OPS.
    range_begin, range_end = map(int, range.split('-'))
    response = ops.published_data_search(
        query, range_begin=range_begin, range_end=range_end, constituents=to_list(constituents))

    # Decode OPS response from JSON
    payload = handle_response(response, 'ops-search')

    if response.headers['content-type'].startswith('application/json'):

        # Decode total number of results.
        pointer_total_count = JsonPointer('/ops:world-patent-data/ops:biblio-search/@total-result-count')
        count_total = int(pointer_total_count.resolve(payload))

        # Raise an exception to skip caching empty results.
        if count_total == 0:
            raise NoResultsException('No results', data=payload)

        return payload


@cache_region('search')
def ops_published_data_crawl(constituents, query, chunksize):

    if constituents != 'pub-number':
        raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

    real_constituents = constituents
    if constituents == 'pub-number':
        constituents = ''

    # fetch first chunk (1-chunksize) from upstream
    first_chunk = ops_published_data_search(constituents, query, '1-{0}'.format(chunksize))
    #print first_chunk

    pointer_total_count = JsonPointer('/ops:world-patent-data/ops:biblio-search/@total-result-count')
    total_count = int(pointer_total_count.resolve(first_chunk))
    log.info('ops_published_data_crawl total_count: %s', total_count)

    # The first 2000 hits are accessible from OPS.
    total_count = min(total_count, 2000)

    # collect upstream results
    begin_second_chunk = chunksize + 1
    chunks = [first_chunk]
    for range_begin in range(begin_second_chunk, total_count + 1, chunksize):

        # countermeasure to robot flagging
        # <code>CLIENT.RobotDetected</code>
        # <message>Recent behaviour implies you are a robot. The server is at the moment busy to serve robots. Please try again later</message>
        time.sleep(5)

        range_end = range_begin + chunksize - 1
        range_string = '{0}-{1}'.format(range_begin, range_end)
        log.info('ops_published_data_crawl range: ' + range_string)
        chunk = ops_published_data_search(constituents, query, range_string)
        #print 'chunk:', chunk
        chunks.append(chunk)

    #return chunks

    # merge chunks into single result
    """
    <empty>:    "ops:search-result" { » "ops:publication-reference": [
    biblio:     "ops:search-result" { » "exchange-documents": [ » "exchange-document": {
    abstract:   "ops:search-result" { » "exchange-documents": [ » "exchange-document": {
    full-cycle: "ops:search-result" { » "exchange-documents": [ » "exchange-document": [
    pub-number: "ops:search-result" { » "ops:publication-reference": [
                        {
                            "@family-id": "6321653",
                            "@system": "ops.epo.org",
                            "document-id": {
                                "@document-id-type": "docdb",
                                "country": {
                                    "$": "DE"
                                },
                                "doc-number": {
                                    "$": "3705908"
                                },
                                "kind": {
                                    "$": "A1"
                                }
                            }
                        },
    """
    pointer_results = JsonPointer('/ops:world-patent-data/ops:biblio-search/ops:search-result/ops:publication-reference')
    #pointer_time_elapsed = JsonPointer('/ops:world-patent-data/ops:meta/@value')
    all_results = []
    #time_elapsed = int(pointer_time_elapsed.resolve(first_chunk))
    for chunk in chunks:

        # FIXME: use this for "real_constituents == 'pub-number'" only
        chunk_results = to_list(pointer_results.resolve(chunk))

        # FIXME: implement other constituents

        #print 'chunk_results:', chunk_results
        all_results += chunk_results

        #time_elapsed += int(pointer_time_elapsed.resolve(chunk))

    response = None
    if real_constituents == 'pub-number':

        response = first_chunk

        # delete upstream data
        del resolve_pointer(response, '/ops:world-patent-data/ops:biblio-search/ops:search-result')['ops:publication-reference']

        # compute own representation
        publication_numbers = []
        pointer_document_id = JsonPointer('/document-id')
        for entry in all_results:
            pubref = pointer_document_id.resolve(entry)
            #print entry, pubref
            pubref_number, pubref_date = _get_document_number_date(pubref, 'docdb')
            publication_numbers.append(pubref_number)

        # add own representation
        set_pointer(response, '/ops:world-patent-data/ops:biblio-search/ops:search-result/publication-numbers', publication_numbers, inplace=True)

        # amend metadata
        new_total_count = str(len(publication_numbers))
        pointer_total_count.set(response, new_total_count)
        set_pointer(response, '/ops:world-patent-data/ops:biblio-search/ops:range', {'@begin': '1', '@end': new_total_count})
        #pointer_time_elapsed.set(response, str(time_elapsed))

    if not response:
        raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

    return response


def image_representative_from_family(patent, countries, func_filter=None):

    log.info('Finding alternative documents for drawings of {patent}'.format(patent=patent))

    document             = patent.country + patent.number + patent.kind
    document_no_kindcode = patent.country + patent.number
    family = ops_family_members(document_no_kindcode)

    # Compute alternative family members sorted by given countries
    alternatives = family.publications_by_country(exclude=[document], countries=countries)
    if func_filter:
        alternatives = filter(func_filter, alternatives)

    if alternatives:
        # TODO: Currently using first item as representative. This might change.
        representative = alternatives[0]
        log.info('Drawings: Amending {document} to {representative} of {alternatives}'.format(**locals()))
        patent.update(decode_patent_number(representative))
        return True

    return False


def image_representative(patent):

    # Amend document number for german Aktenzeichen to Offenlegungsschrift. The former does not carry drawings.
    # Example: DE112013003369A5 to DE102012211542A1
    if patent.country == 'DE' and (patent.kind == 'A5' or patent.kind == 'A8'):
        def kindcode_filter(item):
            return not (item.startswith('DE') and (item.endswith('A5') or item.endswith('A8')))
        image_representative_from_family(patent, ['DE', 'WO'], kindcode_filter)


    # Amend document number for European Search Report to  to Offenlegungsschrift. The former does not carry drawings.
    # Example: EP1929706A4 to EP1929706A1
    elif patent.country == 'EP' and (patent.kind == 'A4'):
        image_representative_from_family(patent, ['EP', 'WO'])


@cache_region('medium')
def inquire_images(document):

    patent = decode_patent_number(document)

    if not patent:
        raise HTTPBadRequest('{0} is not a valid patent number'.format(document))

    image_representative(patent)

    # v1: docdb
    if patent.kind:
        ops_patent = patent['country'] + '.' + patent['number'] + '.' + patent['kind']
        url_image_inquiry_tpl = '{baseuri}/published-data/publication/docdb/images'

    # v2: epodoc
    else:
        ops_patent = patent['country'] + patent['number']
        url_image_inquiry_tpl = '{baseuri}/published-data/publication/epodoc/images'

    url_image_inquiry = url_image_inquiry_tpl.format(baseuri=OPS_API_URI)
    log.debug('Inquire image information via {url}'.format(url=url_image_inquiry))

    error_msg_access = 'No image information for document={0}'.format(document)
    error_msg_process = 'Error while processing image information for document={0}'.format(document)

    # Inquire image metadata from OPS.
    ops = get_ops_client()
    response = ops._make_request(url_image_inquiry, ops_patent)

    # Evaluate response.
    if response.status_code != 200:

        if response.status_code == 404:
            log.warn(error_msg_access)
            error = HTTPNotFound(error_msg_access)
            error.status_code = response.status_code

        else:
            log.error(error_msg_access + '\n' + str(response) + '\n' + str(response.content))
            error = HTTPError(error_msg_access)
            error.status_code = response.status_code

        # TODO: respond with proper json error
        raise error

    try:
        data = response.json()
    except JSONDecodeError as ex:
        # TODO: respond with proper json error
        error_msg_process += ': {0}'.format(str(ex))
        log.error(error_msg_process)
        error = HTTPError(error_msg_process)
        error.status_code = 500
        raise error

    result = data['ops:world-patent-data']['ops:document-inquiry']['ops:inquiry-result']

    info = {}
    for node in to_list(result['ops:document-instance']):

        # Suppress correction pages of amendments like US2010252183A1.
        if is_amendment_only(node): continue

        # Aggregate nodes into map, using the '@desc' attribute as key
        key = node['@desc']
        info[key] = node

    # Enrich image inquiry information. Compute image information for carousel widget.
    enrich_image_inquiry_info(info)

    #log.info('Image info: %s', info)

    return info


def is_fulldocument(node):
    return '@desc' in node and node['@desc'] == u'FullDocument'


def is_amendment_only(node):
    """

    Is FullDocument reference a correction page of amendments like US2010252183A1?

    {u'@desc': u'FullDocument',
         u'@link': u'published-data/images/US/8052819/X6/fullimage',
         u'@number-of-pages': u'1',
         u'@system': u'ops.epo.org',
         u'ops:document-format-options': {u'ops:document-format': [{u'$': u'application/pdf'},
                                                                   {u'$': u'application/tiff'}]},
         u'ops:document-section': {u'@name': u'AMENDMENT',
                                   u'@start-page': u'1'}}],
    """
    if is_fulldocument(node):
        sections = to_list(node.get('ops:document-section', []))
        if len(sections) == 1 and sections[0]['@name'] == u'AMENDMENT':
            return True

    return False


def enrich_image_inquiry_info(info):
    """
    Enrich image inquiry information.
    If DRAWINGS can be properly detected, add information to "meta" dictionary of document and return True.
    """

    meta = {}
    enriched = False

    # Compute page offset to first drawing from "FullDocument" information
    entry = info.get('FullDocument')
    if entry and 'ops:document-section' in entry:
        sections = entry.get('ops:document-section', [])
        for section in to_list(sections):
            if section['@name'] == 'DRAWINGS':
                meta['drawing-start-page'] = int(section['@start-page'])
                enriched = True
                break

    # Compute number of drawing pages
    if 'drawing-start-page' in meta:
        if 'Drawing' in info:
            meta['drawing-total-count'] = int(info['Drawing']['@number-of-pages'])
        else:
            meta['drawing-total-count'] = int(info['FullDocument']['@number-of-pages']) - meta['drawing-start-page'] + 1

    info['META'] = meta

    return enriched


@cache_region('static')
def get_ops_image_pdf(document, page):
    payload = get_ops_image(document, page, 'FullDocument', 'pdf')
    return payload


def get_ops_image(document, page, kind, format):

    # http://ops.epo.org/3.1/rest-services/published-data/images/EP/1000000/PA/firstpage.png?Range=1
    # http://ops.epo.org/3.1/rest-services/published-data/images/US/20130311929/A1/thumbnail.tiff?Range=1

    kind_requested = kind
    if kind_requested == 'FullDocumentDrawing':
        kind = 'FullDocument'

    # 1. Inquire images to compute url to image resource
    image_info = inquire_images(document)
    if image_info:
        if image_info.has_key(kind):
            drawing_node = image_info.get(kind)
            link = drawing_node['@link']

            # compute offset to first drawing if special kind "FullDocumentDrawing" is requested
            if kind_requested == 'FullDocumentDrawing':
                start_page = image_info['META'].get('drawing-start-page')
                if start_page:
                    page = page + start_page - 1

        # fallback chain, if no drawings are available
        elif image_info.has_key('JapaneseAbstract'):
            drawing_node = image_info.get('JapaneseAbstract')
            link = drawing_node['@link']
            page = 1

        else:
            msg = 'No image information for document={0}, kind={1}'.format(document, kind)
            log.warn(msg)
            # TODO: respond with proper json error
            raise HTTPNotFound(msg)

    else:
        msg = 'No image information for document={0}'.format(document)
        #log.warn(msg)
        # TODO: respond with proper json error
        raise HTTPNotFound(msg)

    # Compute document format.
    document_format = 'application/tiff'
    if format == 'pdf':
        document_format = 'application/pdf'

    # Acquire image from OPS.
    ops = get_ops_client()
    response = ops.image(link, range=page, document_format=document_format)

    if response.status_code == 200:

        # Decode and measure content length.
        measure_response(response)

        payload = response.content
        return payload

    else:
        msg = 'Could not load image for document={document}, kind={kind}, page={page}, format={format}'.format(**locals())
        log.error('[{code}] {message}'.format(code=response.status_code, message=msg))
        response = handle_error(response, 'ops-image')
        raise response

    """
    else:
        msg = 'Could not load image for document={document}, kind={kind}, page={page}, format={format}'.format(**locals())
        log.warn('[{code}] {message}'.format(code=response.status_code, message=msg))
        error = HTTPError()
        error.explanation = msg
        error.status_code = response.status_code
        # TODO: respond with proper json error
        raise error
    """


@cache_region('static')
def ops_description(document_number, xml=False):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/description.json
    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666.A2/description.json
    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666.B1/description.json

    url_tpl = '{baseuri}/published-data/publication/epodoc/description'
    url = url_tpl.format(baseuri=OPS_API_URI)

    # Acquire description fulltext from OPS.
    with ops_client(xml=xml) as ops:
        response = ops._make_request(url, document_number)
        return handle_response(response, 'ops-description')


@cache_region('static')
def ops_claims(document_number, xml=False):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/claims.json

    url_tpl = '{baseuri}/published-data/publication/epodoc/claims'
    url = url_tpl.format(baseuri=OPS_API_URI)

    # Acquire claims fulltext from OPS.
    with ops_client(xml=xml) as ops:
        response = ops._make_request(url, document_number)
        return handle_response(response, 'ops-claims')


@cache_region('search')
def ops_family_inpadoc(reference_type, document_number, constituents, xml=False):
    """
    Request family information from OPS in JSON format.

    reference_type = publication|application|priority
    constituents   = biblio|legal

    Examples:
    - http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP.1491501.A1/biblio,legal
    - http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP0666666/biblio
    - http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP0666666.A2/biblio
    - http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP0666666.B1/biblio

    """

    # Compute document identifier.
    document_id = split_patent_number(document_number)
    ops_id = epo_ops.models.Epodoc(document_id.country + document_id.number, document_id.kind)

    # Acquire family information from OPS.
    with ops_client(xml=xml) as ops:
        response = ops.family(reference_type, ops_id, constituents=to_list(constituents))
        return handle_response(response, 'ops-family')


def ops_family_publication_docdb_xml(reference_type, document_number, constituents):
    """
    Request family information from OPS in XML format.

    reference_type = publication|application|priority
    constituents   = biblio|legal

    Examples:
    - http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP.1491501.A1/biblio,legal
    """

    # Compute document identifier.
    document_id = split_patent_number(document_number)
    ops_id = epo_ops.models.Docdb(document_id.number, document_id.country, document_id.kind)

    # Acquire family information from OPS.
    ops = get_ops_client()

    # FIXME: Better use "accept_type" on a per-request basis supported by ``python-epo-ops-client``.
    ops.accept_type = 'application/xml'
    response = ops.family(reference_type, ops_id, constituents=to_list(constituents))
    ops.accept_type = 'application/json'

    return handle_response(response, 'ops-family')


@cache_region('search')
def ops_register(reference_type, document_number, constituents=None, xml=False):
    """
    Request register information from OPS in JSON or XML format.

    reference_type = publication|application|priority

    Examples:
    - http://ops.epo.org/3.1/rest-services/register/publication/epodoc/EP2485810/biblio
    - http://ops.epo.org/3.1/rest-services/register/publication/epodoc/EP2485810/biblio,legal.json
    """

    if constituents is None:
        constituents = 'biblio,legal'

    # Compute document identifier.
    document_id = split_patent_number(document_number)
    #ops_id = epo_ops.models.Docdb(document_id.number, document_id.country, document_id.kind)
    ops_id = epo_ops.models.Epodoc(document_id.country + document_id.number, document_id.kind)

    # Acquire register information from OPS.
    with ops_client(xml=xml) as ops:
        response = ops.register(reference_type, ops_id, constituents=to_list(constituents))
        return handle_response(response, 'ops-register')


def handle_response(response, api_location):
    if response.status_code == 200:

        # Decode and measure content length.
        measure_response(response)

        # Decode body by content type.
        content_type = response.headers['content-type']

        if content_type.startswith('application/json'):
            # Decode OPS response from JSON
            return response.json()

        elif content_type.startswith('application/xml') or content_type.startswith('text/xml'):
            return response.content

        else:
            message = 'OPS service responded with unknown content type "{}"'.format(content_type)
            raise HTTPBadGateway(message)

    else:
        response = handle_error(response, api_location)
        raise response


def measure_response(response):

    # Decode and measure content length.
    content_length = response.headers.get('Content-Length')
    if content_length and content_length.isdigit():
        ops = get_ops_client()
        ops.metrics_manager.measure_upstream('ops', int(content_length))


def handle_error(response, location):
    request = get_current_request()
    response_dict = object_attributes_to_dict(response, ['url', 'status_code', 'reason', 'headers', 'content'])

    # Compute name
    name = 'http-response'
    body = response_dict['content']
    if 'CLIENT.CQL' in body:
        name = 'expression'

    if 'SERVER.DomainAccess' in body or 'EpoqueCommand short-circuited and fallback disabled' in body:
        response_dict['content'] += \
            "<br/><br/>" \
            "The OPS API might be in maintenance mode, this happens regularly at 05:00 a.m. <br/>" \
            "and usually does not last longer than 30 minutes."

    request.errors.add(location, name, response_dict)

    response_json = json_error(request)
    response_json.status = response.status_code

    # countermeasure against "_JSONError: <unprintable _JSONError object>" or the like
    response_json.detail = str(response.status_code) + ' ' + response.reason + ': ' + response.content

    #print "response:", response
    if len(request.errors) == 1:
        error_info = request.errors[0].get('description')
        if error_info.get('status_code') == 404:
            error_content = error_info.get('content', '')
            url = error_info.get('url')
            status = str(error_info.get('status_code', '')) + ' ' + error_info.get('reason', '')

            if 'CLIENT.InvalidCountryCode' in error_content:
                ops_code = 'CLIENT.InvalidCountryCode'
                message = u'OPS API response ({status}, {ops_code}). url={url}'.format(status=status, ops_code=ops_code, url=url)
                log.error(message)
                return response_json

            if 'SERVER.EntityNotFound' in error_content:
                ops_code = 'SERVER.EntityNotFound'
                message = u'OPS API response ({status}, {ops_code}). url={url}'.format(status=status, ops_code=ops_code, url=url)
                log.warning(message)
                return response_json

            if 'OPS - 404' in error_content or 'Page not found' in error_content:
                ops_code = '404 OPS Page not found'
                message = u'OPS API response ({status}, {ops_code}). url={url}'.format(status=status, ops_code=ops_code, url=url)
                log.error(message)
                log.error(u'OPS API errors:\n{}'.format(pformat(request.errors)))
                response_json.status_code = 502
                return response_json

            if 'This API version is not supported' in error_content:
                ops_code = '404 API version not supported'
                message = u'OPS API response ({status}, {ops_code}). url={url}'.format(status=status, ops_code=ops_code, url=url)
                log.error(message)
                response_json.status_code = 502
                return response_json

    log.error(u'OPS API errors:\n{}'.format(pformat(request.errors)))

    return response_json


@cache_region('static')
def pdf_document_build(patent):

    log.info('PDF {}: OPS attempt'.format(patent))

    # 1. collect all single pdf pages
    image_info = inquire_images(patent)
    if not image_info:
        msg = 'No image information for document={0}'.format(patent)
        # TODO: respond with proper json error
        raise HTTPNotFound(msg)

    resource_info = image_info.get('FullDocument')
    if not resource_info:
        msg = 'No image information for document={0}, type=FullDocument'.format(patent)
        raise HTTPNotFound(msg)

    page_count = int(resource_info['@number-of-pages'])
    log.info('OPS PDF builder will collect {0} pages for document {1}'.format(page_count, patent))
    pdf_pages = []
    for page_number in range(1, page_count + 1):
        page = get_ops_image_pdf(patent, page_number)
        pdf_pages.append(page)

    # 2. join single pdf pages
    pdf_document = pdf_join(pages=pdf_pages)

    # 3. add pdf metadata
    page_sections = None
    if resource_info.has_key('ops:document-section'):
        page_sections = resource_info['ops:document-section']
        #pprint(page_sections)

    metadata = pdf_make_metadata(patent, 'ip-navigator:digi42', page_count, page_sections)
    pdf_document = pdf_set_metadata(pdf_document, metadata)

    # TODO: 4. add attachments (e.g. xml)

    return pdf_document


def ops_biblio_documents(patent):
    data = get_ops_biblio_data('publication', patent)
    documents = to_list(data['ops:world-patent-data']['exchange-documents']['exchange-document'])
    return documents


@cache_region('medium')
def get_ops_biblio_data(reference_type, patent, xml=False):

    # Compute document identifier.
    document_id = decode_patent_number(patent)
    if document_id.kind:
        ops_id = epo_ops.models.Docdb(document_id.number, document_id.country, document_id.kind)
    else:
        ops_id = epo_ops.models.Epodoc(document_id.country + document_id.number, document_id.kind)

    # Acquire bibliographic data from OPS.
    with ops_client(xml=xml) as ops:
        response = ops.published_data(reference_type, ops_id, constituents=['full-cycle'])
        return handle_response(response, 'ops-biblio')


@cache_region('medium')
def ops_document_kindcodes(patent):

    error_msg_access = 'No bibliographic information for document={0}'.format(patent)

    log.info('Retrieving kindcodes for document {document}'.format(document=patent))
    documents = ops_biblio_documents(patent)

    kindcodes = []
    for document in documents:

        # TODO: check whether a single occurrance of "not found" should really raise this exception
        if document.has_key('@status') and document['@status'] == 'not found':
            error = HTTPNotFound(error_msg_access)
            raise error

        kindcode = document['@kind']
        kindcodes.append(kindcode)

    return kindcodes


def _get_document_number_date(docref, id_type):
    docref_list = to_list(docref)
    for document_id in docref_list:
        if document_id['@document-id-type'] == id_type:
            if id_type == 'epodoc':
                doc_number = document_id['doc-number']['$']
            else:
                doc_number = document_id['country']['$'] + document_id['doc-number']['$'] + document_id['kind']['$']
            date = document_id.get('date', {}).get('$')
            return doc_number, date
    return None, None


def analytics_family(query):

    payload = {}
    family_has_statistics = {}
    family_has_designated_states = {}

    # A. aggregate list of publication numbers
    # http://ops.epo.org/3.1/rest-services/published-data/search/full-cycle/?q=pa=%22MAMMUT%20SPORTS%20GROUP%20AG%22
    # TODO: step through all pages
    response = ops_published_data_search('biblio', query, '1-50')
    pointer_results = JsonPointer('/ops:world-patent-data/ops:biblio-search/ops:search-result/exchange-documents')
    pointer_family_id = JsonPointer('/exchange-document/@family-id')
    pointer_publication_reference = JsonPointer('/exchange-document/bibliographic-data/publication-reference/document-id')

    # A.1 compute distinct list with unique families
    family_representatives = {}
    results = to_list(pointer_results.resolve(response))
    for result in results:
        family_id = pointer_family_id.resolve(result)
        # TODO: currently, use first document as family representative; this could change
        if family_id not in family_representatives:
            document_id_entries = pointer_publication_reference.resolve(result)
            doc_number, date = _get_document_number_date(document_id_entries, 'epodoc')
            if doc_number:
                family_representatives[family_id] = doc_number


    # B. Enrich all family representatives
    # http://ops.epo.org/3.1/rest-services/family/application/docdb/US19288494.xml
    for family_id, document_number in family_representatives.iteritems():

        payload.setdefault(family_id, {})

        # B.1 Aggregate all family members
        try:
             family = ops_family_members(document_number)
             family_members = family.items
             payload[family_id]['family-members'] = family_members
        except Exception as ex:
            request = get_current_request()
            del request.errors[:]
            log.warn('Could not fetch OPS family for {0}'.format(document_number))
            continue

        # B.2 Use first active priority
        for family_member_raw in family.raw:
            if 'priority-claim' not in payload[family_id]:
                for priority_claim in to_list(family_member_raw['priority-claim']):
                    try:
                        if priority_claim['priority-active-indicator']['$'] == 'YES':
                            prio_number, prio_date = _get_document_number_date(priority_claim['document-id'], 'docdb')
                            payload[family_id]['priority-claim'] = {'number-docdb': prio_number, 'date': prio_date}
                    except KeyError:
                        pass

        # B.3 Compute word- and image-counts for EP publication
        for statistics_country in ['EP', 'WO', 'AT', 'CA', 'CH', 'GB', 'ES']:

            if family_id in family_has_statistics:
                break

            for family_member in family_members:
                pubref_number = family_member['publication']['number-epodoc']
                if pubref_number.startswith(statistics_country):
                    statistics = {}

                    # B.3.1 get data about claims
                    try:
                        claims_response = ops_claims(pubref_number)
                        pointer_claims = JsonPointer('/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/claims')
                        claims = pointer_claims.resolve(claims_response)
                        claim_paragraphs = []
                        for part in to_list(claims['claim']['claim-text']):
                            claim_paragraphs.append(part['$'])
                        claim_text = '\n'.join(claim_paragraphs)
                        statistics['claims-language'] = claims['@lang']
                        statistics['claims-words-first'] = len(claim_paragraphs[0].split())
                        statistics['claims-words-total'] = len(claim_text.split())
                        statistics['claims-count'] = len(claim_paragraphs)

                    except Exception as ex:
                        request = get_current_request()
                        del request.errors[:]
                        log.warn('Could not fetch OPS claims for {0}'.format(pubref_number))

                    # B.3.2 get data about description
                    try:
                        description_response = ops_description(pubref_number)
                        pointer_description = JsonPointer('/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/description')
                        descriptions = pointer_description.resolve(description_response)
                        description_paragraphs = []
                        for part in to_list(descriptions['p']):
                            description_paragraphs.append(part['$'])
                        description_text = '\n'.join(description_paragraphs)
                        statistics['description-words-total'] = len(description_text.split())

                    except Exception as ex:
                        request = get_current_request()
                        del request.errors[:]
                        log.warn('Could not fetch OPS description for {0}'.format(pubref_number))


                    if statistics:

                        # B.3.3 get data about image count
                        try:
                            pubref_number_docdb = family_member['publication']['number-docdb']
                            imginfo = inquire_images(pubref_number_docdb)
                            statistics['drawings-count'] = imginfo['META']['drawing-total-count']

                        except Exception as ex:
                            request = get_current_request()
                            del request.errors[:]

                        family_member['statistics'] = statistics
                        family_has_statistics[family_id] = True
                        break

        # B.4 compute designated states
        pointer_designated_states = JsonPointer('/ops:world-patent-data/ops:register-search/reg:register-documents/reg:register-document/reg:bibliographic-data/reg:designation-of-states')
        for country in ['EP', 'WO']:

            if family_id in family_has_designated_states:
                break

            for family_member in family_members:
                pubref_number = family_member['publication']['number-epodoc']
                if pubref_number.startswith(country):
                    try:
                        reginfo_payload = ops_register('publication', pubref_number, 'biblio')
                    except:
                        request = get_current_request()
                        del request.errors[:]
                        log.warn('Could not fetch OPS register information for {0}'.format(pubref_number))
                        continue

                    designated_states_list = pointer_designated_states.resolve(reginfo_payload)
                    designated_states_info = to_list(designated_states_list)[0]
                    try:
                        regional_info = designated_states_info['reg:designation-pct']['reg:regional']
                        family_member.setdefault('register', {})
                        family_member['register']['designated-states'] = {
                            'gazette-num': designated_states_info['@change-gazette-num'],
                            'region': regional_info['reg:region']['reg:country']['$'],
                            'countries': list(_flatten_ops_json_list(regional_info['reg:country'])),
                        }
                        family_has_designated_states[family_id] = True
                        break

                    except Exception as ex:
                        log.error('Retrieving designated states for {0} failed.'.format(pubref_number))


    return payload


def ops_family_members(document_number):

    pointer_results = JsonPointer('/ops:world-patent-data/ops:patent-family/ops:family-member')
    pointer_publication_reference = JsonPointer('/publication-reference/document-id')
    pointer_application_reference = JsonPointer('/application-reference/document-id')
    #pointer_priority_claim_reference = JsonPointer('/priority-claim/document-id')

    response = ops_family_inpadoc('publication', document_number, '')

    family_members = OPSFamilyMembers()

    family_members.raw = to_list(pointer_results.resolve(response))
    for result in family_members.raw:

        # B.1 get publication and application references
        pubref = pointer_publication_reference.resolve(result)
        pubref_number, pubref_date = _get_document_number_date(pubref, 'docdb')
        pubref_number_epodoc, pubref_date_epodoc = _get_document_number_date(pubref, 'epodoc')
        appref = pointer_application_reference.resolve(result)
        appref_number, appref_date = _get_document_number_date(appref, 'docdb')
        family_members.items.append({
            'publication': {'number-docdb': pubref_number, 'date': pubref_date, 'number-epodoc': pubref_number_epodoc, },
            'application': {'number-docdb': appref_number, 'date': appref_date},
            })

    #log.info('Family members for %s:\n%s', document_number, family_members)

    return family_members


class OPSFamilyMembers(object):

    def __init__(self):
        self.raw = []
        self.items = []

    def __repr__(self):
        return u'<{name} object at 0x{id}>\nitems:\n{items}'.format(name=self.__class__.__name__, id=id(self), items=pformat(self.items))

    def publications_by_country(self, exclude=None, countries=None):
        exclude = exclude or []
        countries = countries or []
        member_publications = []
        for country in countries:
            country = country.upper()
            for member in self.items:
                publication = member['publication']
                if publication['number-docdb'] in exclude or publication['number-epodoc'] in exclude:
                    continue

                publication_number = publication['number-docdb']

                if publication_number.upper().startswith(country):
                    member_publications.append(publication['number-docdb'])

        return member_publications


def _flatten_ops_json_list(ops_list):
    for ops_entry in ops_list:
        yield ops_entry['$']

def _find_publication_number_by_prio_number():
    if 'priority-claim' in payload[family_id]:

        # find publication number by application (prio) number
        prio_number = payload[family_id]['priority-claim']['number']
        pubref_number = None
        for family_member in family_members:
            if family_member['application']['number'] == prio_number:
                pubref_number = family_member['publication']['number']
                break



def _format_title(title):
    return u'[{0}] {1}'.format(title.get(u'@lang', u'').upper() or u'', title[u'$'] or u'')

def _format_abstract(abstract):
    if not abstract: return
    lines = to_list(abstract['p'])
    lines = map(lambda line: line['$'], lines)
    return u'[{0}] {1}'.format(abstract.get(u'@lang', u'').upper() or u'', '\n'.join(lines))

def _mogrify_parties(partylist, name):
    results = []
    parties = {}
    for party in partylist:
        key = party['@sequence']
        parties.setdefault(key, {})
        parties[key][party['@data-format']] = party[name]['name']['$']

    for key in sorted(parties.keys()):
        name_epodoc = parties[key]['epodoc'].replace(u'\u2002', u' ')
        name_original = parties[key]['original']
        entry = u'{0}; {1}'.format(name_epodoc, name_original)
        results.append(entry)

    return results

def _result_list_compact(response):
    items = []

    pointer_results = JsonPointer('/ops:world-patent-data/ops:biblio-search/ops:search-result/exchange-documents')
    pointer_application_reference = JsonPointer('/exchange-document/bibliographic-data/application-reference/document-id')
    pointer_publication_reference = JsonPointer('/exchange-document/bibliographic-data/publication-reference/document-id')
    pointer_invention_title = JsonPointer('/exchange-document/bibliographic-data/invention-title')
    pointer_abstract = JsonPointer('/exchange-document/abstract')
    pointer_applicant = JsonPointer('/exchange-document/bibliographic-data/parties/applicants/applicant')
    pointer_inventor = JsonPointer('/exchange-document/bibliographic-data/parties/inventors/inventor')

    results = to_list(pointer_results.resolve(response))
    for result in results:

        pubref = pointer_publication_reference.resolve(result)
        pubref_number, pubref_date = _get_document_number_date(pubref, 'epodoc')
        pubref_date = pubref_date and '-'.join([pubref_date[:4], pubref_date[4:6], pubref_date[6:8]])

        appref = pointer_application_reference.resolve(result)
        appref_number, appref_date = _get_document_number_date(appref, 'epodoc')
        appref_date = appref_date and '-'.join([appref_date[:4], appref_date[4:6], appref_date[6:8]])

        try:
            titles = to_list(pointer_invention_title.resolve(result))
            titles = map(_format_title, titles)
        except JsonPointerException:
            titles = None

        try:
            abstracts = to_list(pointer_abstract.resolve(result))
            abstracts = map(_format_abstract, abstracts)
        except JsonPointerException:
            abstracts = None

        try:
            applicants = to_list(pointer_applicant.resolve(result))
            applicants = _mogrify_parties(applicants, 'applicant-name')
        except JsonPointerException:
            applicants = None

        try:
            inventors = to_list(pointer_inventor.resolve(result))
            inventors = _mogrify_parties(inventors, 'inventor-name')
        except JsonPointerException:
            inventors = None

        item = {
            'abstract': abstracts,
            'appdate': appref_date,
            'appnumber': appref_number,
            'pubdate': pubref_date,
            'pubnumber': pubref_number,
            'title': titles,
            'applicant': applicants,
            'inventor': inventors,
        }
        items.append(item)

    return items


def _summarize_metrics(payload, kind):

    try:
        metrics = payload['environments'][0]['dimensions'][0]['metrics']
    except KeyError:
        return 'error while computing value'

    total_response_size_entries = filter(lambda item: item['name'] == kind, metrics)[0]['values']
    #print total_response_size_entries

    total_response_sizes = map(lambda item: float(item['value']), total_response_size_entries)
    #print total_response_sizes

    total = sum(total_response_sizes)
    return total


def ops_service_usage(date_begin, date_end):
    client = get_ops_client()

    url = '{baseuri}/me/stats/usage?timeRange={date_begin}~{date_end}'.format(baseuri=OPS_DEVELOPERS_URI, **locals())
    print "getting metrics for:", date_begin, date_end, url
    response = client.get(url)

    #print response
    #print response.headers
    #print response.content

    payload = response.json()

    total_response_size = _summarize_metrics(payload, 'total_response_size')
    message_count = _summarize_metrics(payload, 'message_count')

    data = {
        'time-range':    '{date_begin} to {date_end}'.format(**locals()),
        'response-size': total_response_size,
        'message-count': message_count,
    }

    log.info('OPS service usage for client_id={client_id} from {date_begin} to {date_end} is {data}'.format(
        client_id = client.client_id, **locals()))

    return data


if __name__ == '__main__':
    data = ops_service_usage('06/11/2014', '09/12/2014')
    print 'Time range:    {0}'.format(data['time-range'])
    print 'Response size: {0}G'.format(data['response-size'] / float(10**9))
    print 'Message count: {0}'.format(data['message-count'])
