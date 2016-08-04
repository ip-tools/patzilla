# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG
import types
import logging
import pyparsing
from elmyra.ip.util.cql.pyparsing import CQL
from elmyra.ip.util.cql.pyparsing.parser import CQLGrammar
from elmyra.ip.util.cql.pyparsing.util import walk_token_results
from elmyra.ip.util.date import parse_date_within, iso_to_german, year_range_to_within, iso_to_iso_compact
from elmyra.ip.util.ipc.parser import IpcDecoder
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.util.python import _exception_traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class IFIClaimsGrammar(CQLGrammar):
    def preconfigure(self):
        CQLGrammar.preconfigure(self)
        self.cmp_single = u':'.split()

class IFIClaimsExpression(object):

    """
    Translate discrete comfort form field values to Solr Query Syntax, as convenient as possible.

    https://wiki.apache.org/solr/SolrQuerySyntax
    https://wiki.apache.org/solr/CommonQueryParameters
    https://stackoverflow.com/questions/796753/solr-fetching-date-ranges/796800#796800
    https://cwiki.apache.org/confluence/display/solr/Working+with+Dates
    """

    # map canonical field names to datasource-specific ones
    datasource_indexnames = {
        'patentnumber': 'pn',
        'fulltext':     'text',
        'applicant':    'pa',
        'inventor':     'inv',
        'class':        ['ic', 'cpc'],
        'country':      'pnctry',
        'pubdate':      'pd',
        'appdate':      'ad',
        'citation':     'pcitpn',
    }

    fieldnames = [
        'pn', 'text', 'ic', 'cpc',
        'pnlang', 'pd',

        # Parties
        'pa',
        'inv',
        'apl',
        'asg',
        'reasg',
        'agt',
        'cor',

        # Text
        'text',
        'tac',
        'ttl',
        'ab',
        'desc',
        'clm',
        'aclm',

        # Classifications
        'ic',
        'cpc',
        'ecla',
        'uc',
        'fi',
        'fterm',

        # Filing/Application and priority
        'an',
        'anlang',
        'ad',
        'pri',
        'pridate',
        'regd',

        # International Filing and Publishing data
        'pctan',
        'pctad',
        'pctpn',
        'pctpd',
        'ds',

        # Citations
        'pcit',
        'pcitpn',
        'ncit',

        # Related Documents
        'relan',
        'relad',
        'relpn',
        'relpd',

        # Legal Status Events
        'ls',
        'lsconv',
        'lsrf',
        'lstext',

        # Miscellaneous
        'fam',

    ]

    @classmethod
    def pair_to_solr(cls, key, value, modifiers=None):

        try:
            fieldname = cls.datasource_indexnames[key]
        except KeyError:
            return

        expression = None
        format = u'{0}:{1}'


        # ------------------------------------------
        #   value mogrifiers
        # ------------------------------------------
        if key == 'patentnumber':
            # TODO: parse more sophisticated to make things like "EP666666 or EP666667" or "?query=pn%3AEP666666&datasource=ifi" possible
            # TODO: use different normalization flavor for IFI, e.g. JP01153210A will not work as JPH01153210A, which is required by OPS
            value = normalize_patent(value)

        elif key == 'pubdate':

            """
            - pd:[19800101 TO 19851231]
            - pd:[* TO 19601231]
            - pdyear:[1980 TO 1985]
            - pdyear:[* TO 1960]
            """

            try:

                if len(value) == 4 and value.isdigit():
                    fieldname = 'pdyear'

                # e.g. 1990-2014, 1990 - 2014
                value = year_range_to_within(value)

                if 'within' in value:
                    within_dates = parse_date_within(value)
                    elements_are_years = all([len(value) == 4 and value.isdigit() for value in within_dates.values()])
                    if elements_are_years:
                        fieldname = 'pdyear'

                    parts = []
                    if within_dates['startdate']:
                        within_dates['startdate'] = iso_to_iso_compact(within_dates['startdate'])
                    else:
                        within_dates['startdate'] = '*'

                    if within_dates['enddate']:
                        within_dates['enddate'] = iso_to_iso_compact(within_dates['enddate'])
                    else:
                        within_dates['enddate'] = '*'

                    expression = '{fieldname}:[{startdate} TO {enddate}]'.format(fieldname=fieldname, **within_dates)

                else:
                    value = iso_to_iso_compact(value)

            except Exception as ex:
                message = 'IFI query: Invalid date or range expression "{0}". Reason: {1}'.format(value, ex)
                logger.warn(message + ' Exception was: {0}'.format(_exception_traceback()))
                return {'error': True, 'message': message}

        elif key == 'inventor' or key == 'applicant':
            if not has_booleans(value) and should_be_quoted(value):
                value = u'"{0}"'.format(value)

        elif key == 'class':

            # v1: Naive implementation can only handle single values
            #value = ifi_convert_class(value)

            # v2: Advanced implementation can handle expressions on field "class"
            # Translate class expression from "H04L12/433 or H04L12/24"
            # to "(ic:H04L0012433 OR cpc:H04L0012433) OR (ic:H04L001224 OR cpc:H04L001224)"
            try:

                # Put value into parenthesis, to properly capture expressions
                if value:
                    value = u'({value})'.format(value=value)

                # Parse value as simple query expression
                query_object = CQL(cql=value)

                # Rewrite all patent classifications in query expression ast from OPS format to IFI format
                rewrite_classes_ifi(query_object, format, fieldname)

                # Serialize into appropriate upstream datasource query expression syntax
                expression = query_object.dumps()

            except pyparsing.ParseException as ex:
                return {'error': True, 'message': '<pre>' + str(ex.explanation) + '</pre>'}


        # ------------------------------------------
        #   surround with parentheses
        # ------------------------------------------
        if key in ['fulltext', 'inventor', 'applicant', 'country', 'citation']:
            if has_booleans(value) and not should_be_quoted(value):
                value = u'({0})'.format(value)

        # ------------------------------------------
        #   expression formatter
        # ------------------------------------------
        # Serialize into appropriate upstream datasource query expression syntax
        if not expression:
            expression = format_expression(format, fieldname, value)
            #print 'expression:', expression

        # ------------------------------------------
        #   final polishing
        # ------------------------------------------
        # Solr(?) syntax: boolean operators must be uppercase
        if has_booleans(expression):
            boolis = [' or ', ' and ', ' not ']
            for booli in boolis:
                expression = expression.replace(booli, booli.upper())

        return {'query': expression}


def rewrite_classes_ifi(query_object, format, fieldname):
    """
    Rewrite all patent classifications in query
    expression ast from OPS format to IFI format
    """

    def token_callback(token, *args, **kwargs):

        if len(token) == 1:
            try:
                class_ifi = ifi_convert_class(token[0])
                token[0] = format_expression(format, fieldname, class_ifi)

            except:
                pass

    walk_token_results(query_object.tokens, token_callback=token_callback)

def rewrite_classes_ops(query_object):
    """
    Rewrite all patent classifications in query
    expression ast from IFI format to OPS format
    """

    if not query_object:
        return

    def triple_callback(token, index, binop, term):

        if index in ['ic', 'cpc']:
            try:
                # Decode IPC or CPC class from format "G01F000184"
                patent_class = IpcDecoder(term)

                # Encode IPC or CPC class to format "G01F1/84"
                # token[2] has a reference to "term"
                token[2] = patent_class.formatOPS()

            except:
                pass

    walk_token_results(query_object.tokens, triple_callback=triple_callback)


def format_expression(format, fieldname, value):
    expression = None
    if type(fieldname) in types.StringTypes:
        expression = format.format(fieldname, value)
    elif type(fieldname) is types.ListType:
        subexpressions = []
        for fieldname in fieldname:
            subexpressions.append(format.format(fieldname, value))
        expression = ' or '.join(subexpressions)
        # surround with parentheses
        expression = u'({0})'.format(expression)
    return expression

def ifi_convert_class(value):
    right_truncation = False
    if value.endswith('*'):
        right_truncation = True

    ipc = IpcDecoder(value)
    class_ifi = ipc.formatIFI()
    value = class_ifi

    if right_truncation:
        value += '*'

    return value


# TODO: refactor elsewhere; together with same code from ftpro.search
def has_booleans(value):
    return ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower() or ' to ' in value.lower()

def should_be_quoted(value):
    value = value.strip().lower()
    return\
    '=' not in value and not has_booleans(value) and\
    ' ' in value and value[0] != '"' and value[-1] != '"'
