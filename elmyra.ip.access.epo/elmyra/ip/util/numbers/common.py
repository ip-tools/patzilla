# -*- coding: utf-8 -*-
# (c) 2007-2011 ***REMOVED***
# (c) 2014 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>
from elmyra.ip.util.numbers.helper import strip_spaces
import re

"""
Common lowlevel functions
"""

def join_patent(patent):
    if patent:
        number = patent['country'] + patent['number'] + patent.get('kind', '')
        return number


def split_patent_number(patent_number):

    if not patent_number:
        return


    # set common pattern for splitting patent number into segments

    # pattern evolution
    # e.g. DE12345A1
    #pattern = '^(\D\D)(\d+?)(\D.?)?(_.+)?$'
    # e.g. USPP12009P2
    #pattern = '^(\D\D)(\D{,2}\d+?)(\D.?)?(_.+)?$'
    # e.g. US0PP12009P2
    #pattern = '^(\D\D)(0?\D{,2}\d+?)(\D.?)?(_.+)?$'
    # e.g. DE10001499.2
    #pattern = '^(\D\D)(0?\D{,2}[\d.]+?)([a-zA-Z].?)?(_.+)?$'

    # e.g. DE10001499.2
    pattern = '^(\D\D)(0?\D{,2}[\d.]+?)([a-zA-Z].?)?(_.+)?$'



    # remove leading and trailing space characters
    patent_number = patent_number.strip()

    # pre-flight check for WO applications (let them pass through)

    if patent_number.startswith('WOPCT'):
        patent = {
            'country': 'WO',
            'number': patent_number[2:],
            'kind': '',
            'ext': '',
            }
        return patent

    elif patent_number.startswith('PCT'):
        patent = {
            'country': 'WO',
            'number': patent_number,
            'kind': '',
            'ext': '',
            }
        return patent

    elif patent_number.startswith('AT') and '/' in patent_number:
        patent_number = strip_spaces(patent_number)
        pattern = '^(\D\D)([\d|\/]+?)(\D.?)?(_.+)?$'

    elif patent_number.startswith('JP'):
        pattern = '^(\D\D)([H\d|-]+?)(\D.?)?(_.+)?$'

    else:
        patent_number = modify_invalid_patent_number(patent_number)


    # actually split combined patent number into segments
    r = re.compile(pattern)
    m = r.match(patent_number)
    if m:
        matchnames = ['country', 'number', 'kind', 'ext']

        """
        # statically create parts-hash from matches
        parts = {
          'country': str(m.group(1)),
          'number':  str(m.group(2)),
          'kind':    str(m.group(3)),
          'ext':     str(m.group(4)),
        }
        """

        # dynamically create parts-hash checking whether matches are valid or not
        parts = {}
        for i in range(0, len(matchnames)):
            name = matchnames[i]
            value = ''
            if m.group(i+1):
                value = m.group(i+1)
            parts[name] = value

        return parts


def modify_invalid_patent_number(patent_number):

    # handle special cases (corrupted data?) like "WOWO 99/39395" or "USUS5650746A" (2008-01-23)
    patent_number = patent_number.replace('WOWO', 'WO')
    patent_number = patent_number.replace('USUS', 'US')
    patent_number = patent_number.replace('USDES', 'USD')

    # remove invalid characters
    #r_invalid = re.compile('[\W_]')
    r_invalid = re.compile('[\s_/-]')
    patent_number = r_invalid.sub('', patent_number)

    # make all characters uppercase
    patent_number = patent_number.upper()

    return patent_number
