# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import cornice

from patzilla.util.expression import SearchExpression
from patzilla.util.python import _exception_traceback
from patzilla.access.epo.ops.api import ops_keyword_fields
from patzilla.access.dpma.depatisnet import DpmaDepatisnetAccess

logger = logging.getLogger(__name__)


def cql_prepare_query(query, grammar=None, keyword_fields=None):
    keyword_fields = keyword_fields or ops_keyword_fields + DpmaDepatisnetAccess.keyword_fields
    se = SearchExpression(syntax='cql', grammar=grammar, keyword_fields=keyword_fields)
    se.parse_expression(query)
    return se


def ikofax_prepare_query(query):
    se = SearchExpression(syntax='ikofax')
    se.parse_expression(query)
    return se


def handle_generic_exception(request, ex, backend_name, query):

    if isinstance(ex, cornice.util._JSONError):
        raise ex

    http_response = None
    if hasattr(ex, 'http_response'):
        http_response = ex.http_response

    module_name = ex.__class__.__module__
    class_name = ex.__class__.__name__
    reason = u'{}.{}: {}'.format(module_name, class_name, ex.message)

    logger.critical(u'{backend_name} error: query="{query}", reason={reason}\nresponse:\n{http_response}\nexception:\n{exception}'.format(
        exception=_exception_traceback(), **locals()))

    message = u'An exception occurred while processing your query.<br/>\nReason: {}<br/><br/>\n'.format(reason)
    if module_name == 'pymongo.errors':
        message += 'Error connecting to cache database. Please report this problem to us.'

    return message
