# -*- coding: utf-8 -*-
# (c) 2013-2015 Andreas Motl, Elmyra UG
import re
import json
import logging
from cornice.service import Service
from pyramid.settings import asbool
from pyramid.threadlocal import get_current_request
from elmyra.ip.access.google.search import GooglePatentsExpression
from elmyra.ip.access.serviva.expression import ServivaExpression
from elmyra.ip.access.ftpro.expression import FulltextProExpression
from elmyra.ip.util.cql.util import pair_to_cql
from elmyra.ip.util.expression.keywords import keywords_from_boolean_expression
from elmyra.ip.util.numbers.numberlists import parse_numberlist, normalize_numbers
from elmyra.ip.util.xml.format import pretty_print

log = logging.getLogger(__name__)

query_expression_util_service = Service(
    name='query-expression-utility-service',
    path='/api/util/query-expression',
    description="Query expression utility service")

numberlist_util_service = Service(
    name='numberlist-utility-service',
    path='/api/util/numberlist',
    description="Numberlist utility service")

void_service = Service(
    name='void-service',
    path='/api/void',
    description="Void service")


@query_expression_util_service.post()
def query_expression_util_handler(request):

    # TODO: split functionality between ops/depatisnet, google and ftpro/ftpro
    # TODO: improve error handling

    data = request.json

    return make_expression(data)


def make_expression(data):

    request = get_current_request()

    datasource = data['datasource']
    criteria = data['criteria']
    modifiers = data.get('modifiers', {})
    query = data.get('query')

    if datasource == 'ftpro':
        modifiers = FulltextProExpression.compute_modifiers(modifiers)

    expression = ''
    expression_parts = []
    keywords = []

    if data['format'] == 'comfort':

        if datasource == 'google':
            gpe = GooglePatentsExpression(criteria, query)
            expression = gpe.serialize()
            keywords = gpe.get_keywords()

        else:

            for key, value in criteria.iteritems():

                if not value:
                    continue

                # allow notations like "DE or EP or US" and "DE,EP"
                if key == 'country':
                    entries = re.split('(?: or |,)', value, flags=re.IGNORECASE)
                    entries = [entry.strip() for entry in entries]
                    value = ' or '.join(entries)

                expression_part = None

                if datasource in ['ops', 'depatisnet']:
                    expression_part = pair_to_cql(datasource, key, value)

                elif datasource == 'ftpro':
                    expression_part = FulltextProExpression.pair_to_ftpro_xml(key, value, modifiers)
                    if expression_part:
                        if expression_part.has_key('keywords'):
                            keywords += expression_part['keywords']
                        else:
                            keywords += keywords_from_boolean_expression(key, value)

                elif datasource == 'sdp':
                    expression_part = ServivaExpression.pair_to_solr(key, value, modifiers)
                    if expression_part:
                        if expression_part.has_key('keywords'):
                            keywords += expression_part['keywords']
                        else:
                            keywords += keywords_from_boolean_expression(key, value)

                error_tpl = u'Criteria "{0}: {1}" has invalid format, datasource={2}.'
                if not expression_part:
                    message = error_tpl.format(key, value, datasource)
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                elif expression_part.has_key('error'):
                    message = error_tpl.format(key, value, datasource)
                    message += u'<br/>' + expression_part['message']
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                else:
                    expression_part.get('query') and expression_parts.append(expression_part.get('query'))


    log.info("keywords: %s", keywords)
    request.response.headers['X-Elmyra-Query-Keywords'] = json.dumps(keywords)

    # assemble complete expression from parts, connect them with AND operators
    if datasource in ['ops', 'depatisnet']:
        expression = ' and '.join(expression_parts)

    elif datasource == 'sdp':
        expression = ' AND '.join(expression_parts)

    elif datasource == 'ftpro':
        if expression_parts:
            if len(expression_parts) == 1:
                expression = expression_parts[0]
            else:
                expression = '\n'.join(expression_parts)
                expression = '<and>\n' + expression + '\n</and>'
            expression = pretty_print(expression)

    return expression


@numberlist_util_service.post()
def numberlist_util_handler(request):
    response = {}
    numberlist = None

    if request.content_type == 'text/plain':
        numberlist = parse_numberlist(request.text)
        response['numbers-sent'] = numberlist

    if numberlist:
        if asbool(request.params.get('normalize')):
            response['numbers-normalized'] = normalize_numbers(numberlist)

    return response

