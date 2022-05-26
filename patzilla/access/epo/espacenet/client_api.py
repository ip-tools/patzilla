# -*- coding: utf-8 -*-
# (c) 2015-2022 Andreas Motl <andreas.motl@ip-tools.org>
"""
Data access for EPO/Espacenet, via HTTP API.
https://worldwide.espacenet.com/
"""
import logging

import requests
from beaker.cache import cache_region

from patzilla.util.config import to_list
from patzilla.util.data.container import jpath
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.normalize import normalize_patent


logger = logging.getLogger(__name__)

http = requests.Session()


@cache_region('medium')
def espacenet_fetch_json(document_number, section):
    """
    Acquire data in JSON format from OPS-like API.

    Example:
    https://worldwide.espacenet.com/3.2/rest-services/published-data/publication/docdb/EP0666666B1/biblio.json
    """

    document_number = normalize_patent(document_number, as_string=True, provider='espacenet')

    message_404 = 'No section "{section}" at Espacenet for "{document_number}"'.format(**locals())
    message_fail = 'Fetching section "{section}" from Espacenet for "{document_number}" failed'.format(**locals())

    url_template = "https://worldwide.espacenet.com/3.2/rest-services/published-data/publication/docdb/{}/{}.json"
    url = url_template.format(document_number, section)

    logger.info('Accessing Espacenet: {}'.format(url))
    response = http.get(url, headers={'User-Agent': regular_user_agent})

    if response.status_code == 200:
        return response

    elif response.status_code == 404:
        raise KeyError(message_404)

    else:

        if "SERVER.EntityNotFound" in response.content:
            raise KeyError(message_404)
        else:
            raise ValueError(message_fail)


def espacenet_abstract(document_number):
    """
    Acquire Espacenet "abstract" text from OPS API at worldwide.espacenet.com.

    https://worldwide.espacenet.com/data/publicationDetails/biblio?CC=US&NR=5770123A&DB=worldwide.espacenet.com&FT=D
    https://worldwide.espacenet.com/data/publicationDetails/biblio?CC=DE&NR=19814298A1&DB=worldwide.espacenet.com&FT=D
    https://worldwide.espacenet.com/3.2/rest-services/published-data/publication/docdb/EP0666666B1/biblio.json

    TODO: Impossible to get abstract for document EP0666666B1.
    """

    message_fail = 'Bibliographic data of "{document_number}" at Espacenet lacks "abstract" section'.format(**locals())

    response = espacenet_fetch_json(document_number, 'biblio')
    data = response.json()

    documents = to_list(jpath("/ops:world-patent-data/exchange-documents/exchange-document", data))
    # TODO: Is it sane to only process the first result?
    document = documents[0]

    # Decoder logic taken from `patzilla.access.epo.ops.api._format_abstract`.
    try:
        abstracts = to_list(document["abstract"])
    except KeyError:
        raise KeyError(message_fail)

    results = []
    for abstract in abstracts:
        lines = to_list(abstract['p'])
        lines = map(lambda line: line['$'], lines)
        content = "\n".join(lines)
        lang = abstract.get('@lang')

        item = {
            'xml': content,
            'lang': lang,
            'source': 'espacenet',
        }
        results.append(item)

    try:
        # TODO: Propagate all languages.
        return results[0]
    except IndexError:
        raise KeyError(message_fail)


def espacenet_description_json(document_number):
    """
    Acquire Espacenet "description" fulltext from OPS API at worldwide.espacenet.com.
    ATTENTION: Does not work for US documents and friends.

    https://worldwide.espacenet.com/3.2/rest-services/published-data/publication/docdb/EP0666666B1/description.json
    https://worldwide.espacenet.com/3.2/rest-services/published-data/publication/docdb/US5770123A/description.json

    Does not work for US documents.

    <fault xmlns="http://ops.epo.org">
        <code>CLIENT.InvalidCountryCode</code>
        <message>At least one reference in the request has a unsupported country code: Request for fulltext for FulltextRetrievalType[format=text-only,locale=&lt;null&gt;,reference=OpsPublicationReference[country=&lt;null&gt;,docNumber=US5770123A,kind=&lt;null&gt;,regExKind=&lt;null&gt;,date=&lt;null&gt;,format=epodoc,sequence=0,status=&lt;null&gt;], system [null]] was deemed invalid.</message>
    </fault>
    """

    response = espacenet_fetch_json(document_number, 'description')
    data = response.json()

    # Decoder logic taken from `patzilla.access.epo.ops.api.analytics_family`.
    description = jpath("/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/description", data)
    content = "\n".join(map(lambda line: line['$'], to_list(description['p'])))
    lang = description['@lang']

    item = {
        'xml': content,
        'lang': lang,
        'source': 'espacenet',
    }
    return item
