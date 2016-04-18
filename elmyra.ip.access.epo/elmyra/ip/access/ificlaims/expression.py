# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG
import types
import logging
from elmyra.ip.util.date import parse_date_within, iso_to_german, year_range_to_within, iso_to_iso_compact
from elmyra.ip.util.ipc.parser import IpcDecoder
from elmyra.ip.util.numbers.normalize import normalize_patent
from elmyra.ip.util.python import _exception_traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

            right_truncation = False
            if value.endswith('*'):
                right_truncation = True

            ipc = IpcDecoder(value)
            class_ifi = ipc.formatIFI()
            value = class_ifi

            if right_truncation:
                value += '*'


        # ------------------------------------------
        #   surround with parentheses
        # ------------------------------------------
        if key in ['fulltext', 'inventor', 'applicant', 'country', 'citation']:
            if has_booleans(value) and not should_be_quoted(value):
                value = u'({0})'.format(value)

        # ------------------------------------------
        #   expression formatter
        # ------------------------------------------
        if not expression:
            if type(fieldname) in types.StringTypes:
                expression = format.format(fieldname, value)
            elif type(fieldname) is types.ListType:
                subexpressions = []
                for fieldname in fieldname:
                    subexpressions.append(format.format(fieldname, value))
                expression = ' or '.join(subexpressions)
                # surround with parentheses
                expression = u'({0})'.format(expression)
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


# TODO: refactor elsewhere; together with same code from ftpro.search
def has_booleans(value):
    return ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower() or ' to ' in value.lower()

def should_be_quoted(value):
    value = value.strip().lower()
    return\
    '=' not in value and not has_booleans(value) and\
    ' ' in value and value[0] != '"' and value[-1] != '"'
