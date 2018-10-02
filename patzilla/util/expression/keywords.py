# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import json
import logging

from patzilla.util.cql.pyparsing.parser import wildcards

logger = logging.getLogger(__name__)


def clean_keyword(keyword):
    return keyword.strip(wildcards + ' "()')


def keywords_from_boolean_expression(key, value):
    if key != 'country':
        entries = re.split(' or | and | not ', value, flags=re.IGNORECASE)
        entries = [clean_keyword(entry) for entry in entries]
        return entries

    return []


def compute_keywords(query_object):
    keywords = []
    scan_keywords(query_object, keywords)
    keywords = list(set(keywords))
    return keywords


def scan_keywords(op, keywords):

    # TODO: Move to some ops.py

    if not op: return
    #print "op:", dir(op)

    keyword_fields = [

        # OPS
        'title', 'ti',
        'abstract', 'ab',
        'titleandabstract', 'ta',
        'txt',
        'applicant', 'pa',
        'inventor', 'in',
        'ct', 'citation',

        # classifications
        'ipc', 'ic',
        'cpc', 'cpci', 'cpca', 'cl',

        # application and priority
        'ap', 'applicantnumber', 'sap',
        'pr', 'prioritynumber', 'spr',

        # DEPATISnet
        'ti', 'ab', 'de', 'bi',
        'pa', 'in',
        ]

    if hasattr(op, 'index'):
        #print "op.index:", op.index
        #print "op.term:", op.term
        if str(op.index) in keyword_fields:
            keyword = clean_keyword(unicode(op.term))
            keywords.append(keyword)

    hasattr(op, 'leftOperand') and scan_keywords(op.leftOperand, keywords)
    hasattr(op, 'rightOperand') and scan_keywords(op.rightOperand, keywords)


def keywords_to_response(request, search):
    """
    Propagate keywords to client for highlighting
    """

    logger.info(u'Propagating keywords from "{origin}": {keywords}'.format(
        origin=search.keywords_origin, keywords=search.keywords))

    request.response.headers['X-PatZilla-Query-Keywords'] = json.dumps(search.keywords)
