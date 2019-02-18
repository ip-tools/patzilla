# -*- coding: utf-8 -*-
# (c) 2014-2017 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import urllib2
import cookielib
from BeautifulSoup import BeautifulSoup
from patzilla.util.network.browser import regular_user_agent
from patzilla.util.numbers.common import split_patent_number

log = logging.getLogger(__name__)


def fetch_first_drawing(patent):

    number = patent['country'] + patent['number'] + patent['kind']

    #print "-" * 60
    log.info('USPTO: Fetching first drawing of "{docnumber}"'.format(docnumber=number))

    type = 'patent'

    # analyze document number: determine if publication or patent
    # assume e.g. US2007231208A1 (4+6=10 chars) for publication
    if len(patent['number']) >= 10:
        type = 'publication'

    #type = 'patent'

    # how to handle cookies?
    # http://www.voidspace.org.uk/python/articles/cookielib.shtml

    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

    if type == 'patent':
        baseurls = ['http://patimg1.uspto.gov', 'http://patimg2.uspto.gov']
    elif type == 'publication':
        baseurls = ['http://aiw1.uspto.gov', 'http://aiw2.uspto.gov']

    if type == 'patent':
        url_path = '/.piw?Docid=%s&idkey=NONE' % patent['number']
    elif type == 'publication':
        url_path = '/.aiw?Docid=%s&idkey=NONE' % patent['number']

    for baseurl in baseurls:
        url = baseurl + url_path
        log.info('USPTO: Searching for TIFF document "{docnumber}" at "{url}"'.format(docnumber=number, url=url))
        payload = fetch_first_drawing_do(number, baseurl, url)
        if payload:
            return payload


def fetch_first_drawing_do(number, baseurl, url_initial):

    # 1. fetch and parse initial document page
    html_initial = fetch_url(url_initial)
    if not html_initial:
        log.warning("No content in main document page '%s' (url: %s)" % (number, url_initial))
        return

    soup = BeautifulSoup(html_initial)
    anchors = soup.findAll('a')
    #print anchors

    url_drawing = None
    for anchor in anchors:
        #print "-" * 40
        #print anchor
        #print "href:", anchor['href']
        if "Drawings" in str(anchor):
            #print "yup"
            url_drawing = anchor['href']

    if not url_drawing:
        log.warning("No drawings found in index of screenscraped document '%s'" % number)
        return


    # 2. continue to page of first drawing
    url = baseurl + url_drawing
    html_drawing = fetch_url(url)
    #print html_drawing

    if not html_drawing:
        log.warning("No content for drawing document page '%s' (url: %s)" % (number, url))
        return

    soup = BeautifulSoup(html_drawing)
    embeds = soup.findAll('embed')

    url_tif = None
    if embeds:
        url_tif = embeds[0].get('src')
        #print url_tif

    if not url_tif:
        log.warning("No tif url found in screenscraped document '%s'" % number)
        return


    # 3. fetch tif payload
    url_tif_full = baseurl + url_tif
    log.info("Fetching tif document '%s' from: %s" % (number, url_tif_full))
    tif_payload = fetch_url(url_tif_full)

    if tif_payload:
        length = len(tif_payload)
        #print length
        if length > 7000:
            log.info("Found tif document '%s'. Length: %s" % (number, length))
            return tif_payload
        else:
            log.warning("Tif data length %s below threshold (7000 Bytes)" % length)
            return


def fetch_url(url):

    txdata = None
    txheaders =  {'User-Agent': regular_user_agent}

    # clean up url
    url = url.replace("\r", "")
    url = url.replace("\n", "")

    payload = None
    try:
        req = urllib2.Request(url, txdata, txheaders)
        # create a request object

        handle = urllib2.urlopen(req)
        # and open it to return a handle on the url

        payload = handle.read()

        # workaround to: "urllib2's urlopen() method causes a memory leak"
        # http://bugs.python.org/issue1208304
        handle.fp._sock.recv = None

        handle.close()

    except IOError, e:
        code = None
        reason = None
        if hasattr(e, 'code'):
            code = e.code
        if hasattr(e, 'reason'):
            reason = e.reason
        log.error('We failed to open url "{url}". reason={reason}, code={code}'.format(url=url, reason=reason, code=code))

    return payload


if __name__ == '__main__':

    numbers = [
        #'US20070231208A1', 'US2007231208A1',
        #'US7261559B2',
        #'US07270540B2'
        #'US7493690B2', 'US7494593B1', 'US7494597B2',
        'US20140071615A1', 'US20140075562A1',
        ]
    for number in numbers:
        payload = fetch_first_drawing(split_patent_number(number))
        if payload:
            print "payload length:", len(payload)
        else:
            print "not found"
