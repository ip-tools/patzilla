# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG
from elmyra.ip.util.cql.knowledge import datasource_indexnames
from elmyra.ip.util.date import parse_date_within, iso_to_german

def pair_to_cql(datasource, key, value):

    try:
        fieldname = datasource_indexnames[key][datasource]
    except KeyError:
        return

    cql_part = None
    format = u'{0}=({1})'

    # special processing rules for depatisnet
    if datasource == 'depatisnet':

        if key == 'pubdate':

            if len(value) == 4 and value.isdigit():
                fieldname = 'py'

            elif 'within' in value:
                within_dates = parse_date_within(value)
                elements_are_years = all([len(value) == 4 and value.isdigit() for value in within_dates.values()])
                if elements_are_years:
                    fieldname = 'py'
                cql_part = '{fieldname} >= {startdate} and {fieldname} <= {enddate}'.format(
                    fieldname=fieldname,
                    startdate=iso_to_german(within_dates['startdate']),
                    enddate=iso_to_german(within_dates['enddate']))

            else:
                value = iso_to_german(value)

        elif key == 'inventor' or key == 'applicant':
            value = value.strip(' "')
            if not has_booleans(value) and should_be_quoted(value):
                value = value.replace(' ', '(L)')


    elif datasource == 'ops':

        if key == 'inventor' or key == 'applicant':
            if not has_booleans(value) and should_be_quoted(value):
                value = u'"{0}"'.format(value)

        if 'within' in value:
            format = '{0} {1}'


    if not cql_part:
        cql_part = format.format(fieldname, value)

    return {'query': cql_part}

def has_booleans(value):
    return ' or ' in value.lower() or ' and ' in value.lower() or ' not ' in value.lower()

def should_be_quoted(value):
    value = value.strip()
    return '=' not in value and ' ' in value and value[0] != '"' and value[-1] != '"'
