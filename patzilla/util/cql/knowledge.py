# -*- coding: utf-8 -*-
# (c) 2014-2016 Andreas Motl, Elmyra UG

# values of these indexes will be mangled by patent number normalization
indexes_publication_number = ['pn', 'num']


# map canonical field names to datasource-specific ones
# TODO: Integrate into database adapter, modularize using object composition
datasource_indexnames = {
    'patentnumber': {'ops': 'pn',  'depatisnet': 'pn'},
    'fulltext':     {'ops': 'txt', 'depatisnet': 'bi'},
    'applicant':    {'ops': 'pa',  'depatisnet': 'pa'},
    'inventor':     {'ops': 'in',  'depatisnet': 'in'},
    'class':        {'ops': 'cl',  'depatisnet': 'ic'},
    'country':      {'ops': 'pn',  'depatisnet': 'pc'},
    'pubdate':      {'ops': 'pd',  'depatisnet': {'date': 'pub', 'year': 'py'}},
    'appdate':      {'ops': 'ap',  'depatisnet': {'date': 'ad',  'year': 'ay'}},
    'priodate':     {'ops': None,  'depatisnet': {'date': 'prd', 'year': 'pry'}},
    'citation':     {'ops': 'ct',  'depatisnet': 'ct'},
}
