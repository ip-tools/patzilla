# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
import json
import logging
import cornice
from patzilla.util.cql.pyparsing import CQL
from patzilla.util.cql.util import should_be_quoted
from patzilla.util.data.container import unique_sequence
from patzilla.util.expression.keywords import clean_keyword
from patzilla.util.python import _exception_traceback
from patzilla.access.epo.ops.api import ops_keyword_fields
from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess

log = logging.getLogger(__name__)

def cql_prepare_query(query, grammar=None, keyword_fields=None):

    log.info(u'Parsing search expression "{query}" with grammar "{grammar}"'.format(
        query=query, grammar=grammar and grammar.__name__ or u'default'))

    keyword_fields = keyword_fields or ops_keyword_fields + DpmaDepatisnetAccess.keyword_fields

    # fixup query: wrap into quotes if cql string is a) unspecific, b) contains spaces and c) is still unquoted
    if should_be_quoted(query) and u'within' not in query:
        query = u'"%s"' % query

    # Parse and recompile CQL query string to apply number normalization
    query_object = None
    try:

        # v1: Cheshire3 CQL parser
        #query_object = cql_parse(query)
        #query = query_object.toCQL().strip()

        # v2 pyparsing CQL parser
        query_object = CQL(query, grammar=grammar, keyword_fields=keyword_fields).polish()
        query_recompiled = query_object.dumps()

        if query_recompiled:
            query = query_recompiled

    except Exception as ex:
        # TODO: can we get more details from diagnostic information to just stop here w/o propagating obviously wrong query to OPS?
        log.warn(u'CQL parse error: query="{0}", reason={1}, Exception was:\n{2}'.format(query, ex, _exception_traceback()))

    return query_object, query

def propagate_keywords(request, query_object):
    """propagate keywords to client for highlighting"""
    if query_object:

        try:
            keywords = query_object.keywords()
            origin = 'cql'

        except AttributeError:
            keywords = compute_keywords(query_object)
            origin = 'compute'

        # List of keywords should contain only unique items, if possible
        keywords = unique_sequence(keywords)

        log.info('Propagating keywords from expression "{origin}": {keywords}'.format(origin=origin, keywords=keywords))
        request.response.headers['X-PatZilla-Query-Keywords'] = json.dumps(keywords)

def compute_keywords(query_object):
    keywords = []
    scan_keywords(query_object, keywords)
    keywords = list(set(keywords))
    return keywords

def scan_keywords(op, keywords):

    # TODO: move to some ops.py

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


def handle_generic_exception(request, ex, backend_name, query):

    if isinstance(ex, cornice.util._JSONError):
        raise

    http_response = None
    if hasattr(ex, 'http_response'):
        http_response = ex.http_response

    module_name = ex.__class__.__module__
    class_name = ex.__class__.__name__
    reason = u'{}.{}: {}'.format(module_name, class_name, ex.message)

    log.critical(u'{backend_name} error: query="{query}", reason={reason}\nresponse:\n{http_response}\nexception:\n{exception}'.format(
        exception=_exception_traceback(), **locals()))

    message = u'An exception occurred while processing your query.<br/>\nReason: {}<br/><br/>\n'.format(reason)
    if module_name == 'pymongo.errors':
        message += 'Error connecting to cache database. Please report this problem to us.'

    return message
