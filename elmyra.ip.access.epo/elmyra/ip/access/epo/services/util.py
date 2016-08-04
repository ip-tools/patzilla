# -*- coding: utf-8 -*-
# (c) 2013-2016 Andreas Motl, Elmyra UG
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
from elmyra.ip.access.google.search import GooglePatentsExpression
from elmyra.ip.access.ificlaims.expression import IFIClaimsExpression
from elmyra.ip.access.ftpro.expression import FulltextProExpression
from elmyra.ip.navigator.export import Dossier, DossierXlsx
from elmyra.ip.util.cql.util import pair_to_cql
from elmyra.ip.util.data.container import SmartBunch
from elmyra.ip.util.expression.keywords import keywords_from_boolean_expression
from elmyra.ip.util.numbers.numberlists import parse_numberlist, normalize_numbers
from elmyra.ip.util.xml.format import pretty_print
from elmyra.web.email.submit import email_issue_report

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

    # TODO: split functionality between ops/depatisnet, google and ftpro/ftpro
    # TODO: improve error handling

    data = request.json
    log.info(u'[{userid}] Expression data:  {data}'.format(userid=request.user.userid, data=data))
    expression = make_expression(data)
    log.info(u'[{userid}] Expression query: {expression}'.format(userid=request.user.userid, expression=expression))
    return expression


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

    #if data['format'] == 'comfort':
    if True:

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

                elif datasource == 'ifi':
                    expression_part = IFIClaimsExpression.pair_to_solr(key, value, modifiers)
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


    log.info("Propagating keywords from comfort form: {keywords}".format(keywords=keywords))
    request.response.headers['X-Elmyra-Query-Keywords'] = json.dumps(keywords)

    # assemble complete expression from parts, connect them with AND operators
    if datasource in ['ops', 'depatisnet']:
        expression = ' and '.join(expression_parts)

    elif datasource == 'ifi':
        expression = ' AND '.join(expression_parts)

    elif datasource == 'ftpro':
        if expression_parts:
            if len(expression_parts) == 1:
                expression = expression_parts[0]
            else:
                expression = '\n'.join(expression_parts)
                expression = '<and>\n' + expression + '\n</and>'

            # apply full family mode to whole xml search expression
            if asbool(modifiers.get('family-full')):
                expression = FulltextProExpression.enrich_fullfamily(expression)

            expression = pretty_print(expression, xml_declaration=False)

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

        log.info('Starting data export with format "{format}"'.format(format=output_format))
        data = bunchify(json.loads(request.params.get('json')))

        # Debugging
        #print 'dossier-data:'; pprint(data.toDict())

        payload = None
        if output_format == 'xlsx':

            # Generate rich Workbook
            payload = DossierXlsx(data).create()

            # TODO: Convert Workbook to PDF
            # /Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir /Users/amo/tmp/oo /Users/amo/Downloads/huhu_2016-07-30T22-40-48+02-00.xlsx
            # /Applications/LibreOffice.app/Contents/MacOS/soffice --accept="pipe,name=navigator;urp;" --norestore --nologo --nodefault --headless
            # /Applications/LibreOffice.app/Contents/MacOS/soffice --accept="socket,host=localhost,port=2002;urp;" --norestore --nologo --nodefault --headless

            # /Applications/LibreOffice.app/Contents/program/python
            # import pyoo
            # desktop = pyoo.LazyDesktop(pipe='navigator')
            # doc = desktop.open_spreadsheet('/Users/amo/Downloads/dossier_haha_2016-08-01T07-14-20+02-00 (5).xlsx')
            # doc.save('hello.pdf', filter_name=pyoo.FILTER_PDF_EXPORT)

            # /Applications/LibreOffice.app/Contents/program/LibreOfficePython.framework/bin/unoconv --listener
            # /Applications/LibreOffice.app/Contents/program/LibreOfficePython.framework/bin/unoconv --format=pdf --verbose ~/Downloads/dossier_haha_2016-08-01T07-14-20+02-00.xlsx

        elif output_format == 'csv':
            # TODO: Add comments inline into numberlist
            dossier = Dossier(data)
            payload = dossier.to_csv(dossier.df_documents)

        elif output_format == 'zip':
            dossier = Dossier(data)
            payload = dossier.to_zip(options=data.get('options'))

        else:
            return HTTPBadRequest(u'Export format "{format}" is unknown.'.format(format=output_format))

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
    if 'human' in targets:
        email_issue_report(report)

