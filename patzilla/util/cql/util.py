# -*- coding: utf-8 -*-
# (c) 2013-2018 Andreas Motl <andreas.motl@ip-tools.org>
from patzilla.util.cql.knowledge import datasource_indexnames
from patzilla.util.date import parse_date_within, iso_to_german, year_range_to_within

def pair_to_cql(datasource, key, value):

    try:
        fieldname = datasource_indexnames[key][datasource]
    except KeyError:
        return

    # Sanity checks
    if fieldname is None:
        return

    cql_part = None
    format = u'{0}=({1})'

    # Special processing rules for depatisnet
    if datasource == 'depatisnet':

        if key in ['pubdate', 'appdate', 'priodate']:

            # Date fields for DEPATISnet yield a dictionary here
            fieldinfo = fieldname

            # Assume parsing a regular date
            fieldname = fieldinfo['date']

            # Check if value is a year (4 digits)
            if len(value) == 4 and value.isdigit():
                fieldname = fieldinfo['year']

            # e.g. 1990-2014, 1990 - 2014
            value = year_range_to_within(value)

            if 'within' in value:
                within_dates = parse_date_within(value)

                cql_parts = []
                if within_dates['startdate']:
                    startdate = within_dates['startdate']
                    # Check if value is a year (4 digits)
                    if len(startdate) == 4 and startdate.isdigit():
                        fieldname = fieldinfo['year']
                    part = '{fieldname} >= {startdate}'.format(fieldname=fieldname, startdate=iso_to_german(startdate))
                    cql_parts.append(part)

                if within_dates['enddate']:
                    enddate = within_dates['enddate']
                    # Check if value is a year (4 digits)
                    if len(enddate) == 4 and enddate.isdigit():
                        fieldname = fieldinfo['year']
                    part = '{fieldname} <= {enddate}'.format(fieldname=fieldname, enddate=iso_to_german(enddate))
                    cql_parts.append(part)

                cql_part = ' and '.join(cql_parts)

            else:
                try:
                    value = iso_to_german(value)
                except ValueError as ex:
                    return {'error': True, 'message': ex.message}

        elif key == 'patentnumber' and 1 <= len(value) <= 2:
            fieldname = 'pcod'

        elif key == 'inventor' or key == 'applicant':
            value = value.strip(' "')
            if not has_booleans(value) and should_be_quoted(value):
                value = value.replace(' ', '(L)')

        # 2016-04-19: Improve DEPATISnet convenience by adapting wildcard semantics to world standards
        if '*' in value or '?' in value:
            """
            TRUNCATION/ WILDCARDS
            ? 	no characters to any number of characters
            ! 	precisely one character
            # 	zero or one character

            See also:
            https://depatisnet.dpma.de/prod/en/hilfe/recherchemodi/experten-recherche/index.html

            So, the translation table would be:
            *  ->  ?
            ?  ->  !
            """
            value = value.replace('?', '!')
            value = value.replace('*', '?')


    elif datasource == 'ops':

        if key == 'inventor' or key == 'applicant':
            if not has_booleans(value) and should_be_quoted(value):
                value = u'"{0}"'.format(value)

        if key == 'pubdate':

            # e.g. 1990-2014, 1990 - 2014
            value = year_range_to_within(value)

            if 'within' in value:
                within_dates = parse_date_within(value)
                if not within_dates['startdate'] or not within_dates['enddate']:
                    return {'error': True, 'message': 'OPS only accepts full date ranges in "within" expressions'}

                value = 'within "{startdate},{enddate}"'.format(
                    startdate=within_dates['startdate'],
                    enddate=within_dates['enddate'])

                format = '{0} {1}'

    if not cql_part:
        cql_part = format.format(fieldname, value)

    return {'query': cql_part}

def has_booleans(value):
    return ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower()

def should_be_quoted(value):
    value = value.strip().lower()
    return \
        '=' not in value and not has_booleans(value) and \
        ' ' in value and value[0] != '"' and value[-1] != '"'
