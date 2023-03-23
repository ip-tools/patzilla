# -*- coding: utf-8 -*-
# (c) 2015 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
import re
from patzilla.util.numbers.normalize import normalize_patent

def parse_numberlist(rawdata):
    pattern = re.compile('[,\n]')
    entries = pattern.split(rawdata)
    entries = list(map(str.strip, entries))
    return entries

def normalize_numbers(entries):
    entries = [s.replace(' ', '') for s in entries]
    response = {'valid': [], 'invalid': [], 'all': []}
    for entry in entries:
        entry_normalized = normalize_patent(entry, fix_kindcode=True)
        if entry_normalized:
            response['valid'].append(entry_normalized)
            response['all'].append(entry_normalized)
        else:
            response['invalid'].append(entry)
            response['all'].append(entry)
    return response
