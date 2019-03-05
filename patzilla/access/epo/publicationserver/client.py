# -*- coding: utf-8 -*-
# (c) 2019 The PatZilla Developers
import logging
import requests

from beaker.cache import cache_region
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.network.browser import regular_user_agent
from pyramid.httpexceptions import HTTPNotFound

logger = logging.getLogger(__name__)


@cache_region('static')
def fetch_pdf(document_number):
    """
    Retrieve PDF document from the European publication server.
    https://data.epo.org/publication-server/

    Blueprint address:
    https://data.epo.org/publication-server/pdf-document?cc=EP&pn=nnnnnn&ki=nn
    """

    logger.info('PDF {}: European publication server attempt'.format(document_number))

    patent = normalize_patent(document_number, as_dict=True, provider='espacenet')

    url_tpl = u'https://data.epo.org/publication-server/pdf-document?cc=EP&pn={number}&ki={kind}'

    url = url_tpl.format(**patent)

    logger.info('Accessing EPO publication server: {}'.format(url))
    response = requests.get(url, headers={'User-Agent': regular_user_agent})

    # Debugging
    #print 'response.content:\n', response.content

    if response.status_code == 200:

        if response.headers['Content-Type'] == 'application/pdf':
            payload = response.content
            return payload

        # Sometimes, an appropriate HTML document is returned,
        # pointing to the corresponding WIPO document.
        #
        # Example: EP2706864A2
        # https://data.epo.org/publication-server/pdf-document?cc=EP&pn=2706864&ki=A2
        # http://www.wipo.int/patentscope/search/en/WO2012153305
        #
        # TODO: Unlock this again by leveraging the WIPO URL.
        else:
            msg = 'No PDF document returned from European ' \
                  'publication server for "{document_number}".'.format(**locals())
            logger.warn(msg)
            raise HTTPNotFound(msg)

    else:
        msg = 'No document found at European publication ' \
              'server for "{document_number}"'.format(**locals())
        logger.warn(msg)
        raise HTTPNotFound(msg)


if __name__ == '__main__':
    print fetch_pdf('EP666666A2')
