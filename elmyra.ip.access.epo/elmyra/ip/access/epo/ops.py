# -*- coding: utf-8 -*-
# (c) 2013,2014 Andreas Motl, Elmyra UG
import logging
import operator
from pyramid.httpexceptions import HTTPNotFound, HTTPError, HTTPInternalServerError
from pyramid.threadlocal import get_current_request
from cornice.util import json_error, to_list
from simplejson.scanner import JSONDecodeError
from beaker.cache import cache_region
from jsonpointer import JsonPointer
from elmyra.ip.access.epo.util import object_attributes_to_dict
from elmyra.ip.access.epo.client import oauth_client_create
from elmyra.ip.access.epo.imageutil import pdf_join, pdf_set_metadata, pdf_make_metadata
from elmyra.ip.util.numbers.common import split_patent_number

log = logging.getLogger(__name__)


ops_service_url = 'https://ops.epo.org/3.1/rest-services/'


ops_client = None
def get_ops_client():
    global ops_client
    if not ops_client:
        ops_client = oauth_client_create()
    return ops_client


@cache_region('search')
def ops_published_data_search(constituents, query, range):

    # query EPO OPS REST service
    url_tpl = "https://ops.epo.org/3.1/rest-services/published-data/search/{constituents}"
    url = url_tpl.format(constituents=constituents)

    # v1: anonymous
    #import requests; client = requests

    # v2: with oauth
    client = get_ops_client()

    response = client.get(url, headers={'Accept': 'application/json'}, params={'q': query, 'Range': range})

    # TODO: use POST for large "q" requests, move "Range" to "X-OPS-Range" header
    #response = client.post(url, headers={'Accept': 'application/json'}, data={'q': query})

    #print "request-url:", url
    #print "status-code:", response.status_code
    #print "response:", response
    #print "response body:", response.content


    if response.status_code == 200:
        #print "content-type:", response.headers['content-type']
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            return
    else:
        response = handle_error(response, 'ops-published-data-search')
        raise response


@cache_region('search')
def inquire_images(patent):

    p = split_patent_number(patent)

    # v1: docdb
    patent = p['country'] + '.' + p['number'] + '.' + p['kind']
    url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/docdb/{patent}/images'

    # v2: epodoc
    #patent = p['country'] + p['number']
    #url_image_inquriy_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{patent}/images'

    url_image_inquriy = url_image_inquriy_tpl.format(patent=patent)

    error_msg_access = 'No image information for document={0}'.format(patent)
    error_msg_process = 'Error while processing image information for document={0}'.format(patent)

    client = get_ops_client()
    response = client.get(url_image_inquriy, headers={'Accept': 'application/json'})
    if response.status_code != 200:

        # make 404s cacheable
        # FIXME: really!?
        if response.status_code == 404:
            log.warn(error_msg_access)
            return

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
        key = node['@desc']
        info[key] = node

    enrich_image_inquiry_info(info)

    return info


def enrich_image_inquiry_info(info):
    """enrich image inquiry information"""

    meta = {}

    # compute page offset to first drawing
    entry = info.get('FullDocument')
    if entry and entry.has_key('ops:document-section'):
        sections = entry.get('ops:document-section', [])
        for section in to_list(sections):
            if section['@name'] == 'DRAWINGS':
                meta['drawing-start-page'] = int(section['@start-page'])
                break

    # clone number of drawings
    if meta.has_key('drawing-start-page'):
        if info.has_key('Drawing'):
            meta['drawing-total-count'] = int(info['Drawing']['@number-of-pages'])
        else:
            meta['drawing-total-count'] = int(info['FullDocument']['@number-of-pages']) - meta['drawing-start-page']

    info['META'] = meta


def get_ops_image_link_url(link, format, page=1):
    service_url = ops_service_url
    url_tpl = '{service_url}{link}.{format}?Range={page}'
    url = url_tpl.format(**locals())
    return url


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

    # 1. inquire images to compute url to image resource
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

            url = get_ops_image_link_url(link, format, page)

        # fallback chain, if no drawings are available
        elif image_info.has_key('JapaneseAbstract'):
            drawing_node = image_info.get('JapaneseAbstract')
            link = drawing_node['@link']
            url = get_ops_image_link_url(link, format, 1)

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

    client = get_ops_client()
    response = client.get(url)
    if response.status_code == 200:
        payload = response.content
        return payload

    else:
        msg = 'Could not load image for document={document}, kind={kind}, page={page}, format={format}'.format(**locals())
        log.warn('[{code}] {message}'.format(code=response.status_code, message=msg))
        error = HTTPError()
        error.explanation = msg
        error.status_code = response.status_code
        # TODO: respond with proper json error
        raise error


@cache_region('static')
def ops_description(document_number):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/description.json

    url_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{document_number}/description.json'
    url = url_tpl.format(document_number=document_number)

    client = get_ops_client()
    response = client.get(url, headers={'Accept': 'application/json'})

    if response.status_code == 200:
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            # TODO: handle error here?
            return
    else:
        response = handle_error(response, 'ops-description')
        raise response

@cache_region('static')
def ops_claims(document_number):

    # http://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/EP0666666/claims.json

    url_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/epodoc/{document_number}/claims.json'
    url = url_tpl.format(document_number=document_number)

    client = get_ops_client()
    response = client.get(url, headers={'Accept': 'application/json'})

    if response.status_code == 200:
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            # TODO: handle error here?
            return
    else:
        response = handle_error(response, 'ops-claims')
        raise response


@cache_region('static')
def ops_family_inpadoc(reference_type, document_number, constituents):
    """
    Download requested family publication information from OPS
    e.g. http://ops.epo.org/3.1/rest-services/family/publication/docdb/EP.1491501.A1/biblio,legal

    reference_type = publication|application|priority
    """

    url_tpl = 'https://ops.epo.org/3.1/rest-services/family/{reference_type}/epodoc/{document_number}/{constituents}.json'

    url = url_tpl.format(reference_type=reference_type, document_number=document_number, constituents=constituents)
    client = get_ops_client()
    response = client.get(url, headers={'Accept': 'application/json'})
    #response = client.get(url, headers={'Accept': 'text/xml'})
    #print "response:", response.content

    if response.status_code == 200:
        if response.headers['content-type'] == 'application/json':
            return response.json()
        else:
            # TODO: handle error here?
            return
    else:
        response = handle_error(response, 'ops-family')
        raise response


def handle_error(response, name):
    request = get_current_request()
    response_dict = object_attributes_to_dict(response, ['url', 'status_code', 'reason', 'headers', 'content'])
    response_dict['url'] = response_dict['url'].replace(ops_service_url, '/')

    if 'SERVER.DomainAccess' in response_dict['content']:
        response_dict['content'] += ' (OPS might be in maintenance mode)'

    request.errors.add(name, 'http-response', response_dict)

    response_json = json_error(request.errors)
    response_json.status = response.status_code

    #print "response:", response
    log.warn(request.errors)
    return response_json


@cache_region('static')
def pdf_document_build(patent):

    # 1. collect all single pdf pages
    image_info = inquire_images(patent)
    if not image_info:
        msg = 'No image information for document={0}'.format(patent)
        # TODO: respond with proper json error
        raise HTTPNotFound(msg)

    page_count = int(image_info['FullDocument']['@number-of-pages'])
    log.info('pdf_document_build collecting {0} pages for document {1}'.format(page_count, patent))
    pdf_pages = []
    for page_number in range(1, page_count + 1):
        page = get_ops_image_pdf(patent, page_number)
        pdf_pages.append(page)

    # 2. join single pdf pages
    pdf_document = pdf_join(pages=pdf_pages)

    # 3. add pdf metadata
    page_sections = None
    if image_info['FullDocument'].has_key('ops:document-section'):
        page_sections = image_info['FullDocument']['ops:document-section']
        #pprint(page_sections)

    metadata = pdf_make_metadata(patent, 'digi42, elmyra ip suite', page_count, page_sections)
    pdf_document = pdf_set_metadata(pdf_document, metadata)

    # TODO: 4. add attachments (e.g. xml)

    return pdf_document


@cache_region('search')
def ops_document_kindcodes(patent):

    p = split_patent_number(patent)
    patent = p['country'] + p['number'] # + '.' + p['kind']

    url_biblio_tpl = 'https://ops.epo.org/3.1/rest-services/published-data/publication/docdb/{patent}/biblio/full-cycle'
    url_biblio = url_biblio_tpl.format(patent=patent)

    error_msg_access = 'No bibliographic information for document={0}'.format(patent)
    error_msg_process = 'Error while processing bibliographic information for document={0}'.format(patent)

    client = get_ops_client()
    response = client.get(url_biblio, headers={'Accept': 'application/json'})
    if response.status_code != 200:

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

    documents = to_list(data['ops:world-patent-data']['exchange-documents']['exchange-document'])

    kindcodes = []
    for document in documents:
        #print "document:", document

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
            date = document_id['date']['$']
            return doc_number, date
    return None, None

def ops_analytics_applicant_family(applicant):
    applicant = '"' + applicant.strip('"') + '"'

    payload = {}
    family_has_statistics = {}

    # A. aggregate list of publication numbers
    # http://ops.epo.org/3.1/rest-services/published-data/search/full-cycle/?q=pa=%22MAMMUT%20SPORTS%20GROUP%20AG%22
    # TODO: step through all pages
    response = ops_published_data_search('biblio', 'applicant=' + applicant, '1-10')
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


    # B. aggregate all family members
    # https://ops.epo.org/3.1/rest-services/family/application/docdb/US19288494.xml
    pointer_results = JsonPointer('/ops:world-patent-data/ops:patent-family/ops:family-member')
    pointer_publication_reference = JsonPointer('/publication-reference/document-id')
    pointer_application_reference = JsonPointer('/application-reference/document-id')
    #pointer_priority_claim_reference = JsonPointer('/priority-claim/document-id')
    for family_id, document_number in family_representatives.iteritems():
        payload.setdefault(family_id, {})
        response = ops_family_inpadoc('publication', document_number, '')
        results = to_list(pointer_results.resolve(response))
        family_members = []
        for result in results:

            # B.1 get publication and application references
            pubref = pointer_publication_reference.resolve(result)
            pubref_number, pubref_date = _get_document_number_date(pubref, 'docdb')
            pubref_number_epodoc, pubref_date_epodoc = _get_document_number_date(pubref, 'epodoc')
            appref = pointer_application_reference.resolve(result)
            appref_number, appref_date = _get_document_number_date(appref, 'docdb')
            family_members.append({
                'publication': {'number-docdb': pubref_number, 'date': pubref_date, 'number-epodoc': pubref_number_epodoc, },
                'application': {'number-docdb': appref_number, 'date': appref_date},
            })

            # B.2 use first active priority
            if 'priority-claim' not in payload[family_id]:
                for priority_claim in to_list(result['priority-claim']):
                    try:
                        if priority_claim['priority-active-indicator']['$'] == 'YES':
                            prio_number, prio_date = _get_document_number_date(priority_claim['document-id'], 'docdb')
                            payload[family_id]['priority-claim'] = {'number-docdb': prio_number, 'date': prio_date}
                    except KeyError:
                        pass

        payload[family_id]['family-members'] = family_members


        # B.3 compute word- and image-counts for EP publication
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

    return payload


def _find_publication_number_by_prio_number():
    if 'priority-claim' in payload[family_id]:

        # find publication number by application (prio) number
        prio_number = payload[family_id]['priority-claim']['number']
        pubref_number = None
        for family_member in family_members:
            if family_member['application']['number'] == prio_number:
                pubref_number = family_member['publication']['number']
                break


def _summarize_metrics(payload, kind):

    metrics = payload['environments'][0]['dimensions'][0]['metrics']
    total_response_size_entries = filter(lambda item: item['name'] == kind, metrics)[0]['values']
    #print total_response_size_entries

    total_response_sizes = map(lambda item: float(item['value']), total_response_size_entries)
    #print total_response_sizes

    total = sum(total_response_sizes)
    return total

def ops_service_usage():
    client = get_ops_client()

    # one day
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=24/02/2014~24/02/2014')

    # misc
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=01/01/2014~24/02/2014')
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=23/02/2014~04/03/2014')

    # all
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=26/11/2013~04/03/2014')
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=04/03/2014~27/07/2014')
    #response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=27/07/2014~06/11/2014')
    response = client.get('https://ops.epo.org/3.1/developers/me/stats/usage?timeRange=06/11/2014~09/12/2014')

    #print response
    #print response.headers
    #print response.content

    payload = response.json()

    total_response_size = _summarize_metrics(payload, 'total_response_size')
    print 'Total response size: {0}G'.format(total_response_size / float(10**9))

    message_count = _summarize_metrics(payload, 'message_count')
    print 'Total message count: {0}'.format(message_count)

if __name__ == '__main__':
    ops_service_usage()
