# -*- coding: utf-8 -*-
# (c) 2017-2018 Andreas Motl <andreas.motl@ip-tools.org>
import types
import logging
import pyparsing
from patzilla.navigator.services import cql_prepare_query
from patzilla.util.cql.pyparsing import CQL
from patzilla.util.cql.pyparsing.parser import CQLGrammar
from patzilla.util.cql.pyparsing.util import walk_token_results
from patzilla.util.data.container import unique_sequence
from patzilla.util.date import parse_date_within, year_range_to_within, parse_date_universal
from patzilla.util.ipc.parser import IpcDecoder
from patzilla.util.numbers.common import split_patent_number
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.util.python import _exception_traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DepaTechGrammar(CQLGrammar):
    def preconfigure(self):
        CQLGrammar.preconfigure(self)
        self.cmp_single = u':'.split()


class DepaTechParser(object):

    def __init__(self, expression=None, modifiers=None):
        self.expression = expression
        self.search = None
        self.query_object = None
        self.syntax = None

        self.expression = self.expression and self.expression.strip()

    def parse(self):

        if self.query_object:
            return self

        # Parse CQL expression and extract keywords
        self.search = cql_prepare_query(self.expression, grammar=DepaTechGrammar, keyword_fields=DepaTechExpression.fieldnames)
        self.query_object = self.search.cql_parser

        return self

    def rewrite_classes_ops(self):
        # Rewrite all patent classifications from Lucene format to OPS format
        # e.g. "G01F000184" to "G01F1/84"
        rewrite_classes_ops(self.query_object)
        return self

    def dumps(self):
        self.parse()
        return self.query_object.dumps()

    @property
    def keywords(self):

        self.parse()

        if not self.query_object:
            return

        # Extract classes from representation like "IC:H04L0012433"
        self.rewrite_classes_ops()

        keywords = self.query_object.keywords()

        # List of keywords should contain only unique items
        keywords = unique_sequence(keywords)

        return keywords

    @property
    def keywords_origin(self):
        return 'lucene'


class DepaTechExpression(object):

    """
    Translate discrete comfort form field values to Elasticsearch Query Syntax, as convenient as possible.

    - https://depa.tech/api/depa-index/
    - https://confluence.mtc.berlin/display/DPS/es+-+search+API
    - https://www.elastic.co/guide/en/elasticsearch/reference/current/search-uri-request.html
    """

    # TODO:

    # via: DE.000102011105593.A1
    # "KI": "A1"
    # "RN": "BOEHMERT & BOEHMERT, 28209, Bremen, DE"

    # via: WO.000002017017201.A1
    # "NP": "EP15178648"
    # "importId": [
    #   "2017-05-WO"
    # ]

    # Publication number, e.g. "US.000000009407879.B2"
    # "AN": "US14845439",
    # "DE": "9407879",

    # map canonical field names to datasource-specific ones
    datasource_indexnames = {

        # Will be transformed by custom logic into distinct fields PC, DE, KI
        'patentnumber': None,

        # TODO
        #'applicationnumber': 'AN',
        #'prioritynumber': 'NP',

        'fulltext':     ['AB', 'GT', 'ET', 'FT'],
        'applicant':    'PA',
        'inventor':     'IN',
        'class':        ['IC', 'NC'],
        'country':      'PC',
        'pubdate':      'DP',
        'appdate':      'AD',
        #'citation':     None,
    }

    fieldnames = [

        # Parties
        'PA',
        'IN',

        # Text
        'AB',
        'GT',
        'ET',
        'FT',

        # Classifications
        'IC',
        'ICA',
        'MC',
        'NC',

        # Filing/Application and priority
        'AN',
        #'PC',      # We don't want keywords for two-letter country-codes

        # International Filing and Publishing data
        'DP',
        'AD',

    ]

    @classmethod
    def pair_to_elasticsearch(cls, key, value, modifiers=None):

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

            # Transform into distinct fields PC, DE, KI

            #if has_booleans(value):
            #    value = '({})'.format(value)

            expression_parts = []

            # Publication number
            patent = split_patent_number(value)

            patent_normalized = normalize_patent(patent, for_ops=False)
            if patent_normalized:
                patent = patent_normalized

            if patent:
                subexpression = u'PC:{country} AND DE:{number}'.format(**patent)
                if patent['kind']:
                    subexpression += u' AND KI:{kind}'.format(**patent)
                expression_parts.append(u'({})'.format(subexpression))

            # Application number
            subexpression = u'AN:{}'.format(value)
            expression_parts.append(subexpression)
            expression = u' OR '.join(expression_parts)

            # Priority number
            subexpression = u'NP:{}'.format(value)
            expression_parts.append(subexpression)
            expression = u' OR '.join(expression_parts)

        elif key == 'pubdate':

            """
            - DP:[19800101 TO 19851231]
            - DP:[* TO 19601231]
            """

            try:

                parsed = False

                # e.g. 1991
                if len(value) == 4 and value.isdigit():
                    value = u'within {}0101,{}1231'.format(value, value)

                # e.g. 1990-2014, 1990 - 2014
                value = year_range_to_within(value)

                # e.g.
                # within 1978,1986
                # within 1900,2009-08-20
                # within 2009-08-20,2011-03-03
                if 'within' in value:
                    within_dates = parse_date_within(value)

                    if within_dates['startdate']:
                        if len(within_dates['startdate']) == 4:
                            within_dates['startdate'] += '0101'
                        within_dates['startdate'] = parse_date_universal(within_dates['startdate']).format('YYYYMMDD')
                    else:
                        within_dates['startdate'] = '*'

                    if within_dates['enddate']:
                        if len(within_dates['enddate']) == 4:
                            within_dates['enddate'] += '1231'
                        within_dates['enddate'] = parse_date_universal(within_dates['enddate']).format('YYYYMMDD')
                    else:
                        within_dates['enddate'] = '*'

                    expression = '{fieldname}:[{startdate} TO {enddate}]'.format(fieldname=fieldname, **within_dates)

                elif not parsed:
                    value_date = parse_date_universal(value)
                    if value_date:
                        value = value_date.format('YYYYMMDD')
                    else:
                        raise ValueError(value)

            except Exception as ex:
                message = 'depatech query: Invalid date or range expression "{0}". Reason: {1}.'.format(value, ex)
                logger.warn(message + ' Exception was: {0}'.format(_exception_traceback()))
                return {'error': True, 'message': message}

        elif key == 'inventor' or key == 'applicant':
            if not has_booleans(value) and should_be_quoted(value):
                value = u'"{0}"'.format(value)

        elif key == 'class':

            # v1: Naive implementation can only handle single values
            #value = lucene_convert_class(value)

            # v2: Advanced implementation can handle expressions on field "class"
            # Translate class expression from "H04L12/433 or H04L12/24"
            # to "(ic:H04L0012433 OR cpc:H04L0012433) OR (ic:H04L001224 OR cpc:H04L001224)"
            try:

                # Put value into parenthesis, to properly capture expressions
                if value:
                    value = u'({value})'.format(value=value)

                # Parse value as simple query expression
                query_object = CQL(cql=value)

                # Rewrite all patent classifications in query expression ast from OPS format to Lucene format
                rewrite_classes_lucene(query_object, format, fieldname)

                # Serialize into appropriate upstream datasource query expression syntax
                expression = query_object.dumps()

            except pyparsing.ParseException as ex:
                return {'error': True, 'message': '<pre>' + str(ex.explanation) + '</pre>'}

        elif key == 'country':
            value = value.upper()

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


def rewrite_classes_lucene(query_object, format, fieldname):
    """
    Rewrite all patent classifications in query
    expression ast from OPS format to Lucene format
    """

    def token_callback(token, *args, **kwargs):

        if len(token) == 1:
            try:
                class_lucene = lucene_convert_class(token[0])
                token[0] = format_expression(format, fieldname, class_lucene)

            except:
                pass

    walk_token_results(query_object.tokens, token_callback=token_callback)

def rewrite_classes_ops(query_object):
    """
    Rewrite all patent classifications in query
    expression ast from Lucene format to OPS format
    """

    if not query_object:
        return

    def triple_callback(token, index, binop, term):

        if index in ['IC', 'ICA', 'MC', 'NC']:
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

def lucene_convert_class(value):
    right_truncation = False
    if value.endswith('*'):
        right_truncation = True

    ipc = IpcDecoder(value)
    value = ipc.formatLucene()

    if right_truncation:
        value += '*'

    return value


# TODO: refactor elsewhere; together with same code from sip.client
def has_booleans(value):
    return ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower() or ' to ' in value.lower()

def should_be_quoted(value):
    value = value.strip().lower()
    return\
    '=' not in value and not has_booleans(value) and\
    ' ' in value and value[0] != '"' and value[-1] != '"'


if __name__ == '__main__':
    print DepaTechParser('IC:G01F000184').keywords
