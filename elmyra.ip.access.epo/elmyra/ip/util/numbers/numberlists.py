# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
from elmyra.ip.util.numbers.normalize import normalize_patent

def parse_numberlist(rawdata):
    pattern = re.compile(u'[,\n]')
    entries = pattern.split(rawdata)
    entries = map(unicode.strip, entries)
    return entries

def normalize_numbers(entries):
    entries = map(lambda s: s.replace(u' ', u''), entries)
    response = {'valid': [], 'invalid': []}
    for entry in entries:
        entry_normalized = normalize_patent(entry)
        if entry_normalized:
            response['valid'].append(entry_normalized)
        else:
            response['invalid'].append(entry)
    return response
