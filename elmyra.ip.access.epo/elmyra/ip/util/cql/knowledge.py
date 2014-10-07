# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG

# values of these indexes will be mangled by patent number normalization
indexes_publication_number = ['pn', 'num']

# values of these indexes will be considered keywords
indexes_keywords = [

    # OPS
    'title', 'ti',
    'abstract', 'ab',
    'titleandabstract', 'ta',
    'txt',
    'applicant', 'pa',
    'inventor', 'in',
    'inventorandapplicant', 'ia',

    'ct', 'citation',

    # classifications
    'ipc', 'ic',
    'cpc', 'cpci', 'cpca', 'cl',

    # application and priority
    'ap', 'applicantnumber', 'sap',
    'pr', 'prioritynumber', 'spr',

    # DEPATISnet
    'ti', 'pa', 'in',
    'ab', 'de', 'cl', 'bi',

]

# map canonical field names to datasource-specific ones
datasource_indexnames = {
    'patentnumber': {'ops': 'pn',  'depatisnet': 'pn'},
    'fulltext':     {'ops': 'txt', 'depatisnet': 'bi'},
    'applicant':    {'ops': 'pa',  'depatisnet': 'pa'},
    'inventor':     {'ops': 'in',  'depatisnet': 'in'},
    'class':        {'ops': 'cl',  'depatisnet': 'ic'},
    'country':      {'ops': 'pn',  'depatisnet': 'pc'},
    'pubdate':      {'ops': 'pd',  'depatisnet': 'pub'},
    'appdate':      {'ops': 'ap',  'depatisnet': 'ap'},
    'citation':     {'ops': 'ct',  'depatisnet': 'ct'},
}

ftpro_xml_expression_templates = {
    'patentnumber': '<patentnumber>{value}</patentnumber>',
    'fulltext':     '<text searchintitle="true" searchinabstract="true" searchinclaim="true" searchindescription="true" fullfamily="true">{value}</text>',
    'applicant':    '<applicant type="epo,inpadoc,original">{value}</applicant>',
    'inventor':     '<inventor type="epo,inpadoc,original">{value}</inventor>',
    'pubdate':      {
        'both': '<date type="publication" startdate="{startdate}" enddate="{enddate}" />',
        'startdate': '<date type="publication" startdate="{startdate}" />',
        'enddate': '<date type="publication" enddate="{enddate}" />',
    }
}
