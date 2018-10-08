# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
import re
import json
import logging
import mimetypes
from pprint import pprint
from bunch import bunchify
from cornice.service import Service
from pyramid.settings import asbool
from pyramid.threadlocal import get_current_request
from pyramid.httpexceptions import HTTPServerError, HTTPBadRequest
from patzilla.navigator.export import Dossier, DossierXlsx
from patzilla.util.config import read_list
from patzilla.util.cql.util import pair_to_cql
from patzilla.util.data.container import SmartBunch
from patzilla.util.expression.keywords import keywords_from_boolean_expression
from patzilla.util.numbers.numberlists import parse_numberlist, normalize_numbers
from patzilla.util.python import exception_traceback
from patzilla.util.xml.format import pretty_print
from patzilla.util.web.email.submit import email_issue_report

log = logging.getLogger(__name__)

query_expression_util_service = Service(
    name='query-expression-utility-service',
    path='/api/util/query-expression',
    description="Query expression utility service")

numberlist_util_service = Service(
    name='numberlist-utility-service',
    path='/api/util/numberlist',
    description="Numberlist utility service")

export_util_service = Service(
    name='export-utility-service',
    path='/api/util/export/{kind}.{format}',
    description="Export utility service")

issue_reporter_service = Service(
    name='issue-reporter-service',
    path='/api/util/issue/report',
    description="Issue reporter service")

void_service = Service(
    name='void-service',
    path='/api/void',
    description="Void service")


@query_expression_util_service.post()
def query_expression_util_handler(request):

    # TODO: split functionality between ops/depatisnet, google and sip
    # TODO: improve error handling

    data = request.json
    log.info(u'[{userid}] Expression data:  {data}'.format(userid=request.user.userid, data=data))
    expression_data = make_expression_filter(data)
    log.info(u'[{userid}] Expression query: {expression_data}'.format(userid=request.user.userid, expression_data=expression_data))
    return expression_data


def make_expression_filter(data):

    request = get_current_request()

    datasource = data['datasource']
    criteria = data['criteria']
    modifiers = data.get('modifiers', {})
    query = data.get('query')

    # TODO: Refactor to "patzilla.access.{sip,ificlaims,depatech,google}" namespaces
    if datasource == 'ificlaims':
        from patzilla.access.ificlaims.expression import IFIClaimsExpression
    elif datasource == 'depatech':
        from patzilla.access.depatech.expression import DepaTechExpression
    elif datasource == 'sip':
        from patzilla.access.sip.expression import SipExpression
    elif datasource == 'google':
        from patzilla.access.google.search import GooglePatentsExpression

    if datasource == 'sip':
        modifiers = SipExpression.compute_modifiers(modifiers)

    expression = ''
    expression_parts = []
    filter_parts = []
    keywords = []

    #if data['format'] == 'comfort':
    if True:

        # TODO: Refactor to "patzilla.access.google" namespace
        if datasource == 'google':
            gpe = GooglePatentsExpression(criteria, query)
            expression = gpe.serialize()
            keywords = gpe.get_keywords()

        else:

            # Bring criteria in order: Process "fulltext" first
            keys = criteria.keys()
            if 'fulltext' in keys:
                keys.remove('fulltext')
                keys.insert(0, 'fulltext')

            for key in keys:

                # Acquire humanized expression
                value = criteria.get(key)

                # Sanitize value
                value = value.strip()

                if not value:
                    continue

                # Allow notations like "DE or EP or US" and "DE,EP"
                if key == 'country':
                    entries = re.split('(?: or |,)', value, flags=re.IGNORECASE)
                    entries = [entry.strip() for entry in entries]
                    value = ' or '.join(entries)

                expression_part = None
                filter_part = None

                if datasource in ['ops', 'depatisnet']:
                    expression_part = pair_to_cql(datasource, key, value)

                # TODO: Refactor to "patzilla.access.sip" namespace
                elif datasource == 'sip':
                    expression_part = SipExpression.pair_to_sip_xml(key, value, modifiers)
                    if expression_part:
                        if expression_part.has_key('keywords'):
                            keywords += expression_part['keywords']
                        else:
                            keywords += keywords_from_boolean_expression(key, value)

                # TODO: Refactor to "patzilla.access.ificlaims" namespace
                elif datasource == 'ificlaims':

                    if key == 'pubdate':
                        expression_part = {'empty': True}
                        filter_part = IFIClaimsExpression.pair_to_solr(key, value, modifiers)

                    else:
                        expression_part = IFIClaimsExpression.pair_to_solr(key, value, modifiers)
                        if expression_part:
                            if expression_part.has_key('keywords'):
                                keywords += expression_part['keywords']
                            else:
                                keywords += keywords_from_boolean_expression(key, value)

                # TODO: Refactor to "patzilla.access.depatech" namespace
                elif datasource == 'depatech':

                    expression_part = DepaTechExpression.pair_to_elasticsearch(key, value, modifiers)
                    if expression_part:
                        if expression_part.has_key('keywords'):
                            keywords += expression_part['keywords']
                        else:
                            keywords += keywords_from_boolean_expression(key, value)

                # Accumulate expression part
                error_tpl = u'Criteria "{0}: {1}" has invalid format, datasource={2}.'
                if not expression_part:
                    message = error_tpl.format(key, value, datasource)
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                elif 'error' in expression_part:
                    message = error_tpl.format(key, value, datasource)
                    message += u'<br/>' + expression_part['message']
                    log.warn(message)
                    request.errors.add('query-expression-utility-service', 'comfort-form', message)

                else:
                    query = expression_part.get('query')
                    if query:
                        expression_parts.append(query)

                # Accumulate filter part
                error_tpl = u'Filter "{0}: {1}" has invalid format, datasource={2}.'
                if filter_part:

                    if 'error' in filter_part:
                        message = error_tpl.format(key, value, datasource)
                        message += u'<br/>' + filter_part['message']
                        log.warn(message)
                        request.errors.add('query-expression-utility-service', 'comfort-form', message)

                    else:
                        filter_part.get('query') and filter_parts.append(filter_part.get('query'))


    log.info("Propagating keywords from comfort form: {keywords}".format(keywords=keywords))
    request.response.headers['X-PatZilla-Query-Keywords'] = json.dumps(keywords)

    # assemble complete expression from parts, connect them with AND operators
    if datasource in ['ops', 'depatisnet']:
        expression = ' and '.join(expression_parts)

    elif datasource in ['ificlaims', 'depatech']:
        expression = ' AND '.join(expression_parts)

    elif datasource == 'sip':
        if expression_parts:
            if len(expression_parts) == 1:
                expression = expression_parts[0]
            else:
                expression = '\n'.join(expression_parts)
                expression = '<and>\n' + expression + '\n</and>'

            # apply full family mode to whole xml search expression
            if asbool(modifiers.get('family-full')):
                expression = SipExpression.enrich_fullfamily(expression)

            expression = pretty_print(expression, xml_declaration=False)

    payload = {
        'expression': expression,
        'filter': ' AND '.join(filter_parts),
    }

    return payload


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

def request_to_options(request, options):

    # TODO: transfer all modifiers 1:1

    if asbool(request.params.get('query_data[modifiers][family-remove]')):
        options.update({'feature_family_remove': True})
    elif asbool(request.params.get('query_data[modifiers][family-replace]')):
        options.update({'feature_family_replace': True})

    # this is awful, switch to JSON POST
    for key, value in request.params.iteritems():
        if key.startswith(u'query_data[sorting]'):
            key = key.replace('query_data[sorting]', '').replace('[', '').replace(']', '')
            options.setdefault('sorting', {})
            options['sorting'][key] = value


@export_util_service.post(renderer='null')
def export_util_handler(request):

    #print 'request.matchdict:', request.matchdict

    output_kind   = request.matchdict['kind']
    output_format = request.matchdict['format']

    # Convert numberlists to Excel
    if output_kind == 'numberlist':
        numberlist = parse_numberlist(request.params.get('numberlist'))

        payload = create_xlsx({'numberlist': numberlist})

        # Export buffer to HTTP response
        filename = '{0}.xlsx'.format('numberlist')
        mimetype, encoding = mimetypes.guess_type(filename, strict=False)

        request.response.content_type = mimetype
        request.response.charset = None
        request.response.headers['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=filename)

        #response['numberlist'] = numberlist

        # Send as response
        return payload

    elif output_kind == 'dossier':

        log.info('Starting dossier export to format "{format}"'.format(format=output_format))
        data = bunchify(json.loads(request.params.get('json')))

        # Debugging
        #print 'dossier-data:'; pprint(data.toDict())

        payload = None
        try:
            if output_format == 'xlsx':
                # Generate Office Open XML Workbook
                payload = DossierXlsx(data).create()

            elif output_format == 'pdf':
                # Generate Office Open XML Workbook and convert to PDF
                dossier = DossierXlsx(data)
                payload = dossier.to_pdf()

            elif output_format == 'csv':
                # TODO: Add comments inline into numberlist
                dossier = Dossier(data)
                payload = dossier.to_csv(dossier.df_documents)

            elif output_format == 'zip':
                dossier = Dossier(data)
                payload = dossier.to_zip(request=request, options=data.get('options'))

            else:
                return HTTPBadRequest(u'Export format "{format}" is unknown.'.format(format=output_format))

        except Exception as ex:
            message = u'Exporting format "{format}" failed.'.format(format=output_format)
            log.error('{message}. Exception:\n{trace}'.format(message=message, trace=exception_traceback()))
            return HTTPServerError(message)

        # Send HTTP response
        filename = 'dossier_{name}_{timestamp}.{format}'.format(
            name=data.get('name', 'default'),
            timestamp=data.get('project', {}).get('modified'),
            format=output_format)
        mimetype, encoding = mimetypes.guess_type(filename, strict=False)

        request.response.content_type = mimetype
        request.response.charset = None
        request.response.headers['Content-Disposition'] = 'attachment; filename={filename}'.format(filename=filename)

        return payload

    # TODO: Log request
    log.error('Data export error')

    # TODO: Proper error page for user to report this problem.
    raise HTTPServerError('Data export error. Please contact support.')




@issue_reporter_service.post()
def issue_reporter_handler(request):

    targets = request.params.get('targets')

    report_data = request.json
    report_data.setdefault('application', {})
    report = SmartBunch.bunchify(report_data)

    # Add user information to issue report
    user = request.user
    if user:

        # Anonymize sensitive user data
        user.password = None
        user.upstream_credentials = None

        # Serialize user object and attach to report
        report.application.user = SmartBunch(json.loads(user.to_json()))

    # Send the whole beast to the standard application log
    log.error('Issue report [{targets}]:\n{report}'.format(
        report=report.pretty(),
        targets=targets
    ))

    # TODO: Store the issue report into database
    # TODO: What about other targets like "log:error", "log:warning", "human:support", "human:user"?

    # Send email report
    for target in read_list(targets):
        if target.startswith('email:'):
            recipient = target.replace('email:', '')
            email_issue_report(report, recipient)

