# -*- coding: utf-8 -*-
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
from patzilla.util.cql.pyparsing.parser import wildcards

def clean_keyword(keyword):
    return keyword.strip(wildcards + ' "()')

def keywords_from_boolean_expression(key, value):
    if key != 'country':
        entries = re.split(' or | and | not ', value, flags=re.IGNORECASE)
        entries = [clean_keyword(entry) for entry in entries]
        return entries

    return []
