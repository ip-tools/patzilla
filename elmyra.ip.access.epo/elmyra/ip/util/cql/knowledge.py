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
